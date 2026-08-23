"""
A minimal text viewer/editor shown inside a directory pane, in place of the
file list. Triggered by the "View file" command (see core/commands/__init__.py
- ViewFile) via show_text_viewer(pane, url), which reads `url` from disk.
Enter/double-click still open files with the OS default app; this is a
separate, palette-only path. Opens read-only; a viewer-scoped command palette
(Ctrl+Shift+P, see PaneTextView) can switch it to editable for files that are
safe to write back (see core.textviewer_io.is_editable). show_text_in_viewer
is a read-only sibling that mounts arbitrary text with no backing file - see
core/commands/release_notes.py and docs/views/RELEASE_NOTES.md.
"""
from core.key_bindings import (
	dispatch_bindable_command, format_shortcut_hint, get_shortcuts_for_command,
	VIEWER_KEY_BINDINGS_FILE,
)
from core.quicksearch_matchers import contains_chars
from core.textviewer_io import (
	MAX_VIEW_BYTES as _MAX_VIEW_BYTES, read_text_for_view, load_for_view,
)
from core.textviewer_pane import (
	caret_fix_css, confirm_close, begin_new_view, mount_view,
	close_view as close_text_viewer,
)
from core.textviewer_reload import reload_from_disk
from core.textviewer_watch import toggle_auto_reload, toggle_tail
from core.textviewer_zoom import (
	get_saved_view_font_size, change_view_font_size, reset_view_font_size,
	zoom_delta_for,
)
from fman import (
	show_alert, show_prompt, show_quicksearch, show_status_message,
	QuicksearchItem, YES, NO, load_json,
)
from fman.fs import notify_file_changed
from fman.impl.util.qt.key_event import QtKeyEvent
from fman.impl.util.qt.thread import run_in_main_thread
from fman.url import as_human_readable
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPlainTextEdit

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
		self._watcher = None
		self._tail = False
		self._set_read_only()
		self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
		self.setStyleSheet(caret_fix_css(bg, fg, get_saved_view_font_size()))
	def keyPressEvent(self, event):
		if (event.key() == Qt.Key_P and event.modifiers() & Qt.ControlModifier
				and event.modifiers() & Qt.ShiftModifier):
			# Own palette, not fman's global Ctrl+Shift+P: the global one
			# only fires on the (now hidden) file list, and this one should
			# list viewer-only actions anyway.
			self._open_palette()
			return
		key_event = QtKeyEvent(event.key(), event.modifiers())
		key_bindings = load_json('Key Bindings.json', default=[])
		zoom_delta = zoom_delta_for(key_event, key_bindings)
		if zoom_delta is not None:
			# Whatever the user has increase/decrease pane font size bound
			# to (default Alt+Up/Down) also zooms the viewer - works in both
			# view and edit mode, and is checked before the edit-mode
			# passthrough below so it never gets typed into the buffer.
			change_view_font_size(self, self._apply_font_size, zoom_delta)
			return
		# Checked before the edit-mode passthrough (same reasoning as zoom
		# above) so e.g. a user-bound Ctrl+S works while typing; unbound
		# keys still fall through to normal typing. Viewer pseudo-commands
		# are looked up in their own file, separate from the zoom binding
		# above - see core.key_bindings.VIEWER_KEY_BINDINGS_FILE.
		viewer_bindings = load_json(VIEWER_KEY_BINDINGS_FILE, default=[])
		if dispatch_bindable_command(key_event, viewer_bindings, self._bindable_commands()):
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

	def _bindable_commands(self):
		# Viewer-only pseudo-commands this focused view matches against
		# Viewer Key Bindings.json itself (see keyPressEvent) - not registered
		# DirectoryPaneCommands, not in Core's own Key Bindings.json. Mirrors
		# _get_actions's mode split so a bound key does the same thing its
		# palette entry does. viewer_switch_panes is deliberately absent in
		# edit mode - Tab must keep typing normally there (see keyPressEvent).
		if self._editing:
			return {
				'text_save': self._save,
				'text_save_as': self._save_as,
				'text_revert': self._revert,
				'viewer_close': self._exit_with_dirty_check,
				'viewer_open_palette': self._open_palette,
			}
		commands = {
			'text_edit': self._enter_edit_mode,
			'text_reload': self._revert,
			'viewer_close': self._on_close,
			'viewer_switch_panes': self._on_switch,
			'viewer_open_palette': self._open_palette,
		}
		if self._path is not None:
			commands['text_toggle_auto_reload'] = lambda: toggle_auto_reload(self)
			commands['text_toggle_tail'] = lambda: toggle_tail(self)
		return commands

	def _apply_font_size(self, size):
		# Passed as the apply_size callback to core.textviewer_zoom, which
		# stays PyQt/stylesheet-agnostic; size=None clears the override.
		self.setStyleSheet(caret_fix_css(self._bg, self._fg, size))

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
		watching = self._watcher is not None
		reload_actions = []
		if self._path is not None:
			auto_label = (
				'Disable auto-reload' if watching and not self._tail
				else 'Enable auto-reload'
			)
			tail_label = (
				'Disable tail mode' if watching and self._tail
				else 'Enable tail mode (follow end)'
			)
			reload_actions = [
				(auto_label, lambda: toggle_auto_reload(self), ''),
				(tail_label, lambda: toggle_tail(self), ''),
			]
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
			] + reload_actions + zoom_actions + [
				('Exit viewer', self._exit_with_dirty_check, ''),
			]
		return [
			('Exit viewer', self._on_close, ''),
			('Edit file', self._enter_edit_mode, ''),
			('Reload from disk', self._revert, ''),
		] + reload_actions + zoom_actions

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
		reload_from_disk(self, tail=False)

	def _exit_with_dirty_check(self):
		if confirm_close(self):
			self._on_close()

	def _set_read_only(self):
		self.setReadOnly(True)
		# setReadOnly(True) alone leaves the cursor unable to move at all via
		# the keyboard in this Qt build (verified: Right/Shift+Right are
		# silently no-ops without this) — not just editing-disabled, as the
		# name implies. Explicit flags restore keyboard navigation/selection
		# while keeping the widget non-editable. Shared by __init__ and
		# _revert (a reload that turns out non-editable falls back here too).
		self.setTextInteractionFlags(
			Qt.TextSelectableByKeyboard | Qt.TextSelectableByMouse
		)

def _mount_new_view(pane, text, path, url, editable):
	# Shared by show_text_viewer/show_text_in_viewer below - both build a
	# PaneTextView the same way and only differ in what they pass in.
	prepared = begin_new_view(pane)
	if prepared is None:
		return
	widget, bg, fg = prepared
	view = PaneTextView(
		lambda: close_text_viewer(widget),
		lambda: pane.run_command('switch_panes'),
		bg, fg, path, url, editable,
	)
	view.setPlainText(text)
	mount_view(pane, widget, view)

@run_in_main_thread
def show_text_viewer(pane, url):
	path = as_human_readable(url)
	text, editable = load_for_view(path)
	_mount_new_view(pane, text, path, url, editable)

@run_in_main_thread
def show_text_in_viewer(pane, text):
	"""
	Shows arbitrary read-only text in the pane's viewer widget, with no
	backing file — used by the "Release Notes" command (core/commands/
	release_notes.py) to render a release's notes without writing a temp
	file. Always read-only (there's nothing to save back to), unlike
	show_text_viewer where editability depends on the source file.
	"""
	_mount_new_view(pane, text, None, None, False)
