"""
The label of a ProgressDialog while a copy runs on several workers: the main
text, one line per worker and buttons that add or remove a worker.

QProgressDialog only lays out a label, a bar and a cancel button. Putting the
extra widgets inside its label - a QLabel with a layout of its own - keeps
everything else ProgressDialog does: the delayed show, cancel and alerts. Lives
outside widgets.py, which is close to the analyzer's line limit.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout

class WorkersLabel(QLabel):
	def __init__(self, workers):
		super().__init__()
		self._workers = workers
		self._row_count = None
		self._text = QLabel()
		# ponytail: one text line per worker. Add a bar per worker if the
		# percentages prove too coarse.
		self._rows = QLabel()
		self._count = QLabel()
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
		layout.addWidget(self._rows)
		layout.addLayout(buttons)
		self.refresh('')
	def refresh(self, text):
		"""
		Returns whether the number of rows changed, so the dialog must resize.
		"""
		workers = self._workers.snapshot()
		self._text.setText(text)
		self._rows.setText('\n'.join(map(_describe, workers)))
		active = sum(1 for worker in workers if not worker.retiring)
		self._count.setText('Threads: %d' % active)
		self._remove.setEnabled(self._workers.can_remove())
		self._add.setEnabled(self._workers.can_add())
		changed = self._row_count is not None and \
			len(workers) != self._row_count
		self._row_count = len(workers)
		return changed
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

def _describe(worker):
	result = '#%d  %s' % (worker.id, worker.title or '(idle)')
	if worker.title and worker.size:
		result += '  %d%%' % (100 * worker.progress // worker.size)
	if worker.retiring:
		result += '  (finishing)'
	return result
