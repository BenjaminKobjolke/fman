"""
A minimal read-only image viewer shown inside a directory pane, in place of
the file list - the "View file" command's image counterpart to
core/textviewer.py's PaneTextView (see ViewFile in core/commands/__init__.py,
which routes to whichever viewer matches the file's extension via
is_image()). Reuses core/textviewer_pane.py's pane-mounting glue
(begin_new_view/mount_view/close_view) as-is; the only shared-code change is
confirm_close() tolerating a view with no `_editing` attribute of its own.
"""
from core.imageviewer_zoom import (
	change_image_scale, get_saved_scale, reset_image_scale, save_scale,
)
from core.key_bindings import (
	dispatch_bindable_command, format_shortcut_hint, get_shortcuts_for_command,
	KEY_BINDINGS_FILE, VIEWER_KEY_BINDINGS_FILE,
)
from core.textviewer_pane import begin_new_view, mount_view, close_view as close_text_viewer
from core.textviewer_zoom import zoom_delta_for
from core.viewer_navigation import open_viewer_palette, ViewerNavigator
from fman import load_json
from fman.impl.util.qt.key_event import QtKeyEvent
from fman.impl.util.qt.thread import run_in_main_thread
from fman.url import as_human_readable
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QImageReader, QMovie, QPixmap
from PyQt5.QtWidgets import QFrame, QLabel, QScrollArea

IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.ico', '.svg')

def is_image(url):
	return url.lower().endswith(IMAGE_EXTENSIONS)

class PaneImageView(QScrollArea):
	def __init__(self, on_close, on_switch, pane, bg, path):
		super().__init__()
		self._on_close = on_close
		self._on_switch = on_switch
		self._nav = ViewerNavigator(pane, 'image')
		self._scale = get_saved_scale()
		self._movie = None
		self._pixmap = None
		self._label = QLabel()
		self._label.setAlignment(Qt.AlignCenter)
		self.setWidget(self._label)
		self.setAlignment(Qt.AlignCenter)
		self.setFrameShape(QFrame.NoFrame)
		# Same QSS-local-rule trick as caret_fix_css (textviewer_pane.py):
		# a type-selector rule beats the app-wide Theme.css `*` wildcard,
		# letterboxing the pane in the live file-view background color
		# (bg, from begin_new_view's palette) instead of a hardcoded one.
		self.setStyleSheet('QScrollArea, QLabel { background-color: %s; }' % bg)
		self._original_size = QImageReader(path).size()
		if path.lower().endswith('.gif'):
			self._movie = QMovie(path)
			self._label.setMovie(self._movie)
			self._movie.start()
		else:
			self._pixmap = QPixmap(path)
			if self._original_size.isEmpty():
				self._original_size = self._pixmap.size()

	def effective_scale(self):
		# The scale actually on screen right now: the explicit override if
		# one's set, else whatever fit-to-viewport currently computes to.
		# Used by change_image_scale as the base to step from so zooming in
		# from fit mode doesn't jump straight to 1.25x.
		if self._scale is not None:
			return self._scale
		if self._original_size.isEmpty():
			return 1.0
		fitted_width = self._original_size.scaled(
			self.viewport().size(), Qt.KeepAspectRatio
		).width()
		return fitted_width / self._original_size.width()

	def resizeEvent(self, event):
		super().resizeEvent(event)
		self._render()

	def keyPressEvent(self, event):
		if (event.key() == Qt.Key_P and event.modifiers() & Qt.ControlModifier
				and event.modifiers() & Qt.ShiftModifier):
			# Own palette, not fman's global Ctrl+Shift+P - see
			# PaneTextView.keyPressEvent for why.
			self._open_palette()
			return
		key_event = QtKeyEvent(event.key(), event.modifiers())
		key_bindings = load_json(KEY_BINDINGS_FILE, default=[])
		zoom_delta = zoom_delta_for(key_event, key_bindings)
		if zoom_delta is not None:
			change_image_scale(self, self._apply_scale, zoom_delta)
			return
		# A user rebind always wins over the hardcoded defaults below -
		# checked first for that reason. Viewer pseudo-commands are looked
		# up in their own file, separate from the zoom binding above - see
		# core.key_bindings.VIEWER_KEY_BINDINGS_FILE.
		viewer_bindings = load_json(VIEWER_KEY_BINDINGS_FILE, default=[])
		if dispatch_bindable_command(key_event, viewer_bindings, self._bindable_commands()):
			return
		if event.key() in (
			Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Backspace
		):
			self._on_close()
			return
		if event.key() in (Qt.Key_Tab, Qt.Key_Backtab):
			self._on_switch()
			return
		# Anything else (notably arrow keys) falls through to QScrollArea's
		# own handling, which pans via the scrollbars once zoomed in past
		# the viewport size.
		super().keyPressEvent(event)

	def _bindable_commands(self):
		# Viewer-only pseudo-commands this focused view matches against
		# Viewer Key Bindings.json itself (see keyPressEvent) - not registered
		# DirectoryPaneCommands, not in Core's own Key Bindings.json. Zoom
		# in/out are deliberately not here: they already follow the pane
		# font-size binding via zoom_delta_for, checked above.
		return {
			'image_reset_zoom': self._fit_to_window,
			'image_actual_size': self._actual_size,
			'viewer_close': self._on_close,
			'viewer_switch_panes': self._on_switch,
			'viewer_open_palette': self._open_palette,
			**self._nav.commands(),
		}

	def _apply_scale(self, scale):
		self._scale = scale
		self._render()

	def _render(self):
		if self._original_size.isEmpty():
			return
		if self._scale is not None:
			target = QSize(
				max(1, round(self._original_size.width() * self._scale)),
				max(1, round(self._original_size.height() * self._scale)),
			)
		else:
			target = self._original_size.scaled(self.viewport().size(), Qt.KeepAspectRatio)
		if self._movie is not None:
			self._movie.setScaledSize(target)
		else:
			self._label.setPixmap(self._pixmap.scaled(
				target, Qt.KeepAspectRatio, Qt.SmoothTransformation
			))
		self._label.resize(target)

	def _open_palette(self):
		open_viewer_palette(self._get_actions)

	def _get_actions(self):
		key_bindings = load_json(KEY_BINDINGS_FILE, default=[])
		zoom_in_hint = format_shortcut_hint(
			get_shortcuts_for_command(key_bindings, 'increase_pane_font_size')
		)
		zoom_out_hint = format_shortcut_hint(
			get_shortcuts_for_command(key_bindings, 'decrease_pane_font_size')
		)
		return [
			('Fit to window', self._fit_to_window, ''),
			('Actual size (100%)', self._actual_size, ''),
			(
				'Zoom in',
				lambda: change_image_scale(self, self._apply_scale, +1),
				zoom_in_hint,
			),
			(
				'Zoom out',
				lambda: change_image_scale(self, self._apply_scale, -1),
				zoom_out_hint,
			),
			('Reset zoom', self._fit_to_window, ''),
		] + self._nav.actions() + [
			('Exit viewer', self._on_close, ''),
		]

	def _fit_to_window(self):
		reset_image_scale(self._apply_scale)

	def _actual_size(self):
		save_scale(1.0)
		self._apply_scale(1.0)

@run_in_main_thread
def show_image_viewer(pane, url, focus_view=True):
	prepared = begin_new_view(pane)
	if prepared is None:
		return
	widget, bg, _fg = prepared
	path = as_human_readable(url)
	view = PaneImageView(
		lambda: close_text_viewer(widget),
		lambda: pane.run_command('switch_panes'),
		pane, bg, path,
	)
	mount_view(pane, widget, view, focus_view=focus_view)
