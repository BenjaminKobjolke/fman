"""
A minimal text viewer/editor shown inside a directory pane, in place of the
file list. Triggered by the "View file" command (see core/commands/__init__.py
- ViewFile). Enter/double-click still open files with the OS default app;
this is a separate, palette-only path. Opens read-only; a viewer-scoped
command palette (Ctrl+Shift+P, see PaneTextView) can switch it to editable
for files that are safe to write back (see core.textviewer_io.is_editable).
"""
from core.key_bindings import get_shortcuts_for_command, format_shortcut_hint
from core.quicksearch_matchers import contains_chars
from core.textviewer_io import (
	MAX_VIEW_BYTES as _MAX_VIEW_BYTES, read_text_for_view, load_for_view,
)
from core.textviewer_zoom import (
	get_saved_view_font_size, change_view_font_size, reset_view_font_size,
	zoom_delta_for,
)
from fman import (
	show_alert, show_prompt, show_quicksearch, show_status_message,
	QuicksearchItem, YES, NO, CANCEL, load_json,
)
from fman.fs import notify_file_changed
from fman.impl.util.qt.key_event import QtKeyEvent
from fman.impl.util.qt.thread import run_in_main_thread
from fman.url import as_human_readable
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QPlainTextEdit

# Once the app-wide Theme.css ("* { font-size: ...pt; }", applied via
# QApplication.setStyleSheet) touches a widget, Qt switches that widget from
# palette-based rendering to the QSS style engine — and the QSS engine only
# draws the blinking text caret if `color`/`background-color` are set
# explicitly; otherwise it silently stops drawing it. This mirrors the same
# wildcard-rule problem the font-size feature works around for the file list
# (`FileListView { font-size: ...pt; }`, commands/__init__.py) — a local
# type-selector override wins over the global `*` rule. `bg`/`fg` are read
# from the live file view's palette (see show_text_viewer) so the viewer
# always matches the pane colors, whatever theme set them. `font_size`, when
# given, is the viewer's own zoom override (see _change_view_font_size) —
# folded into the same local rule so it likewise beats the wildcard `*` rule.
def _caret_fix_css(bg, fg, font_size=None):
	css = 'QPlainTextEdit { color: %s; background-color: %s;' % (fg, bg)
	if font_size is not None:
		css += ' font-size: %dpt;' % font_size
	return css + ' }'

def _confirm_close(view):
	"""
	If `view` is mid-edit with unsaved changes, asks to save/discard/cancel.
	Returns True if it's fine to proceed with closing or replacing the view
	(nothing unsaved, or the user just saved/discarded), False if the caller
	must abort (user cancelled). Shared by PaneTextView._exit_with_dirty_check
	and show_text_viewer(), which otherwise would silently drop unsaved edits
	when a second "View file" replaces the currently open buffer.
	"""
	if not (view._editing and view.document().isModified()):
		return True
	answer = show_alert('Save changes before closing?', YES | NO | CANCEL, YES)
	if answer & CANCEL:
		return False
	if answer & YES:
		view._save()
	return True

class PaneTextView(QPlainTextEdit):
	def __init__(self, on_close, on_switch, bg, fg, path, url, editable):
		super().__init__()
		self._on_close = on_close
		self._on_switch = on_switch
		self._bg = bg
		self._fg = fg
		self._path = path
		self._url = url
		self._editable = editable
		self._editing = False
		self.setReadOnly(True)
		# setReadOnly(True) alone leaves the cursor unable to move at all via
		# the keyboard in this Qt build (verified: Right/Shift+Right are
		# silently no-ops without this) — not just editing-disabled, as the
		# name implies. Explicit flags restore keyboard navigation/selection
		# while keeping the widget non-editable:
		self.setTextInteractionFlags(
			Qt.TextSelectableByKeyboard | Qt.TextSelectableByMouse
		)
		self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
		self.setStyleSheet(_caret_fix_css(bg, fg, get_saved_view_font_size()))
	def keyPressEvent(self, event):
		if (event.key() == Qt.Key_P and event.modifiers() & Qt.ControlModifier
				and event.modifiers() & Qt.ShiftModifier):
			# Own palette, not fman's global Ctrl+Shift+P: the global one
			# only fires on the (now hidden) file list, and this one should
			# list viewer-only actions anyway.
			self._open_palette()
			return
		key_event = QtKeyEvent(event.key(), event.modifiers())
		zoom_delta = zoom_delta_for(key_event, load_json('Key Bindings.json', default=[]))
		if zoom_delta is not None:
			# Whatever the user has increase/decrease pane font size bound
			# to (default Alt+Up/Down) also zooms the viewer - works in both
			# view and edit mode, and is checked before the edit-mode
			# passthrough below so it never gets typed into the buffer.
			change_view_font_size(self, self._apply_font_size, zoom_delta)
			return
		if self._editing:
			# Edit mode: everything, including Tab, goes to the editor as
			# normal typing. Exit/save/switch-panes are palette-only while
			# editing, so an accidental keystroke can't discard/lose focus.
			super().keyPressEvent(event)
			return
		if event.key() in (
			Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Backspace
		):
			self._on_close()
			return
		if event.key() in (Qt.Key_Tab, Qt.Key_Backtab):
			# Forward to the pane's own Tab binding (switch_panes) instead of
			# letting QPlainTextEdit swallow it for focus traversal. The
			# viewer stays open; show_text_viewer() re-points the pane's
			# focus proxy at us, so tabbing back re-focuses this view.
			self._on_switch()
			return
		super().keyPressEvent(event)

	def _apply_font_size(self, size):
		# Passed as the apply_size callback to core.textviewer_zoom, which
		# stays PyQt/stylesheet-agnostic; size=None clears the override.
		self.setStyleSheet(_caret_fix_css(self._bg, self._fg, size))

	def _open_palette(self):
		result = show_quicksearch(self._suggest_actions)
		if result:
			_query, action = result
			if action:
				action()

	def _suggest_actions(self, query):
		for title, action, hint in self._get_actions():
			highlight = contains_chars(title.lower(), query.lower())
			if highlight is not None:
				yield QuicksearchItem(action, title, highlight, hint)

	def _get_actions(self):
		key_bindings = load_json('Key Bindings.json', default=[])
		zoom_actions = [
			(
				'Increase font size',
				lambda: change_view_font_size(self, self._apply_font_size, +1),
				format_shortcut_hint(
					get_shortcuts_for_command(key_bindings, 'increase_pane_font_size')
				),
			),
			(
				'Decrease font size',
				lambda: change_view_font_size(self, self._apply_font_size, -1),
				format_shortcut_hint(
					get_shortcuts_for_command(key_bindings, 'decrease_pane_font_size')
				),
			),
			(
				'Reset font size',
				lambda: reset_view_font_size(self._apply_font_size), '',
			),
		]
		if self._editing:
			return [
				('Save file', self._save, ''),
				('Save file as…', self._save_as, ''),
				('Revert / reload from disk', self._revert, ''),
			] + zoom_actions + [
				('Exit viewer', self._exit_with_dirty_check, ''),
			]
		return [
			('Exit viewer', self._on_close, ''),
			('Edit file', self._enter_edit_mode, ''),
			('Reload from disk', self._revert, ''),
		] + zoom_actions

	def _enter_edit_mode(self):
		if not self._editable:
			show_alert(
				"This file can't be edited here: it's either larger than "
				'%d MB or not valid UTF-8 text.'
				% (_MAX_VIEW_BYTES // (1024 * 1024))
			)
			return
		self._editing = True
		self.setReadOnly(False)
		self.setTextInteractionFlags(Qt.TextEditorInteraction)

	def _write(self, path):
		# QPlainTextEdit normalizes all line endings to '\n', so a file
		# originally using CRLF is rewritten with LF on save — a known,
		# accepted limitation (see docs/views/TEXT_VIEWER.md).
		with open(path, 'wb') as f:
			f.write(self.toPlainText().encode('utf-8'))

	def _save(self):
		self._write(self._path)
		notify_file_changed(self._url)
		self.document().setModified(False)
		show_status_message('Saved')

	def _save_as(self):
		new_path, ok = show_prompt('Save as (full path):', default=self._path)
		if not ok or not new_path:
			return
		self._write(new_path)
		self._path = new_path
		notify_file_changed(self._url)
		self.document().setModified(False)
		show_status_message('Saved as %s' % new_path)

	def _revert(self):
		if self._editing and self.document().isModified():
			if not show_alert(
				'Discard unsaved changes and reload from disk?', YES | NO, NO
			) & YES:
				return
		text, editable = load_for_view(self._path)
		self._editable = editable
		self.setPlainText(text)
		self.document().setModified(False)
		if self._editing and not self._editable:
			self._editing = False
			self.setReadOnly(True)
			self.setTextInteractionFlags(
				Qt.TextSelectableByKeyboard | Qt.TextSelectableByMouse
			)

	def _exit_with_dirty_check(self):
		if _confirm_close(self):
			self._on_close()

@run_in_main_thread
def show_text_viewer(pane, url):
	widget = pane._widget
	existing_view = getattr(widget, '_text_view', None)
	if existing_view is not None and not _confirm_close(existing_view):
		# User cancelled out of the save/discard prompt for the file
		# currently open in this pane — leave it open, don't switch files.
		return
	close_text_viewer(widget)
	path = as_human_readable(url)
	text, editable = load_for_view(path)
	palette = widget._file_view.palette()
	bg = palette.color(QPalette.Base).name()
	fg = palette.color(QPalette.Text).name()
	view = PaneTextView(
		lambda: close_text_viewer(widget),
		lambda: pane.run_command('switch_panes'),
		bg, fg, path, url, editable,
	)
	view.setPlainText(text)
	widget.layout().addWidget(view)
	widget._file_view.setVisible(False)
	widget._text_view = view
	# Re-point the pane's focus proxy at the viewer. switch_panes() ends by
	# calling the *other* pane's focus(), which is setFocus() on this pane's
	# widget — following the proxy. Without this it would land back on the
	# hidden file view instead of the viewer when tabbing back.
	widget.setFocusProxy(view)
	# The command palette's modal dialog restores focus to the (now hidden)
	# file view as it closes, right before this function runs. Grabbing
	# focus here immediately gets clobbered by that restore, so the caret
	# never shows. Defer one event-loop tick so we focus after it settles:
	QTimer.singleShot(0, view.setFocus)

@run_in_main_thread
def close_text_viewer(pane_widget):
	view = getattr(pane_widget, '_text_view', None)
	if view is None:
		return
	pane_widget.layout().removeWidget(view)
	view.deleteLater()
	pane_widget._text_view = None
	# Restore the pane's original focus proxy (set in DirectoryPaneWidget
	# .__init__) before the file view reclaims focus.
	pane_widget.setFocusProxy(pane_widget._file_view)
	pane_widget._file_view.setVisible(True)
	pane_widget._file_view.setFocus()
