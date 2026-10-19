"""
The label of a ProgressDialog while a copy runs on several workers: the main
text, one line per worker and buttons that add or remove a worker.

QProgressDialog only lays out a label, a bar and a cancel button. Putting the
extra widgets inside its label - a QLabel with a layout of its own - keeps
everything else ProgressDialog does: the delayed show, cancel and alerts. Lives
outside widgets.py, which is close to the analyzer's line limit.
"""

from fman import QuicksearchItem
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout

class WorkersLabel(QLabel):
	def __init__(self, workers, parent=None):
		super().__init__()
		self._workers = workers
		self._row_count = None
		self._text = QLabel()
		# ponytail: one text line per worker, split into columns so a
		# percentage stays put while file names change. Add a bar per worker
		# if the percentages prove too coarse.
		self._ids = QLabel()
		self._percents = QLabel()
		self._titles = QLabel()
		self._rows = QHBoxLayout()
		for column in (self._ids, self._percents, self._titles):
			column.setAlignment(Qt.AlignLeft | Qt.AlignTop)
			self._rows.addWidget(column)
		self._percents.setAlignment(Qt.AlignRight | Qt.AlignTop)
		self._rows.addStretch()
		self._count = QLabel()
		# Not in this label's layout: the dialog places it under its bar.
		self._files = QLabel(parent)
		self._remove = self._button('−', workers.remove)
		self._add = self._button('+', workers.add)
		buttons = QHBoxLayout()
		buttons.addWidget(self._count)
		buttons.addStretch()
		buttons.addWidget(self._remove)
		buttons.addWidget(self._add)
		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.addWidget(self._text)
		layout.addLayout(self._rows)
		layout.addLayout(buttons)
		self.refresh('')
	def refresh(self, text):
		"""
		Returns whether the number of rows changed, so the dialog must resize.
		"""
		workers = self._workers.snapshot()
		self._text.setText(text)
		ids, percents, titles = _columns(workers)
		self._ids.setText(ids)
		self._percents.setText(percents)
		# Measured here, not in __init__: the stylesheet's font only applies
		# once the label is shown. Fixed, so 0% is as wide as 100%.
		self._percents.setFixedWidth(
			self._percents.fontMetrics().horizontalAdvance('100%')
		)
		self._titles.setText(titles)
		# The columns' layout keeps its cached size hint until the event loop
		# runs. The dialog resizes right away, so it would not grow.
		self._rows.invalidate()
		self._files.setText('%d / %d' % self._workers.counts())
		active = sum(1 for worker in workers if not worker.retiring)
		self._count.setText('Threads: %d' % active)
		self._remove.setEnabled(self._workers.can_remove())
		self._add.setEnabled(self._workers.can_add())
		changed = self._row_count is not None and \
			len(workers) != self._row_count
		self._row_count = len(workers)
		return changed
	def handle_key(self, key):
		"""
		Returns whether the key added or removed a worker.
		"""
		if key in (Qt.Key_Plus, Qt.Key_Up):
			self._workers.add()
		elif key in (Qt.Key_Minus, Qt.Key_Down):
			self._workers.remove()
		else:
			return False
		return True
	def open_palette(self, show_quicksearch, on_cancel):
		# The dialog's own palette, like the viewers': fman's global one only
		# opens from a pane, and it would not list these actions anyway.
		actions = []
		if self._workers.can_add():
			actions.append(('Add thread', '+ / Up', self._workers.add))
		if self._workers.can_remove():
			actions.append(('Remove thread', '- / Down', self._workers.remove))
		actions.append(('Cancel', 'Esc', on_cancel))
		def suggest(query):
			# ponytail: plain substring filter; three rows need no fuzzy match.
			return [
				QuicksearchItem(action, title, hint=hint)
				for title, hint, action in actions
				if query.lower() in title.lower()
			]
		result = show_quicksearch(suggest)
		if result and result[1]:
			result[1]()
	def place_file_count(self, bar, cancel):
		# Under the bar's left side, beside the Cancel button.
		self._files.setGeometry(QRect(
			bar.x(), cancel.y(), cancel.x() - bar.x(), cancel.height()
		))
		self._files.show()
	def sizeHint(self):
		return self.layout().sizeHint()
	def minimumSizeHint(self):
		return self.layout().minimumSize()
	def _button(self, text, on_click):
		result = QPushButton(text)
		# Like the rest of fman's overlays: keep focus where it is.
		result.setFocusPolicy(Qt.NoFocus)
		result.clicked.connect(on_click)
		return result

def _columns(workers):
	# One pass, so the three columns always have the same number of lines.
	ids, percents, titles = [], [], []
	for worker in workers:
		ids.append('#%d' % worker.id)
		percent = ''
		if worker.title and worker.size:
			percent = '%d%%' % (100 * worker.progress // worker.size)
		percents.append(percent)
		title = worker.title or '(idle)'
		if worker.retiring:
			title += '  (finishing)'
		titles.append(title)
	return '\n'.join(ids), '\n'.join(percents), '\n'.join(titles)
