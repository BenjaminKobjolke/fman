"""
Pane-mounting glue for the text viewer (core/textviewer.py): the caret-fix
stylesheet, the unsaved-edit confirmation prompt, and swapping a
PaneTextView into/out of the pane's layout in place of the (hidden) file
list. Split out of core/textviewer.py to stay under the project's 300-line
file cap — genuinely separate from PaneTextView itself (the widget/editor
behaviour) even though both are Qt-touching.
"""
from fman import show_alert, YES, NO, CANCEL
from fman.impl.util.qt.thread import run_in_main_thread
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPalette

# Once the app-wide Theme.css ("* { font-size: ...pt; }", applied via
# QApplication.setStyleSheet) touches a widget, Qt switches that widget from
# palette-based rendering to the QSS style engine — and the QSS engine only
# draws the blinking text caret if `color`/`background-color` are set
# explicitly; otherwise it silently stops drawing it. This mirrors the same
# wildcard-rule problem the font-size feature works around for the file list
# (`FileListView { font-size: ...pt; }`, commands/__init__.py) — a local
# type-selector override wins over the global `*` rule. `bg`/`fg` are read
# from the live file view's palette (see begin_new_view) so the viewer
# always matches the pane colors, whatever theme set them. `font_size`, when
# given, is the viewer's own zoom override (see PaneTextView._apply_font_size)
# — folded into the same local rule so it likewise beats the wildcard `*` rule.
def caret_fix_css(bg, fg, font_size=None):
	css = 'QPlainTextEdit { color: %s; background-color: %s;' % (fg, bg)
	if font_size is not None:
		css += ' font-size: %dpt;' % font_size
	return css + ' }'

def confirm_close(view):
	"""
	If `view` is mid-edit with unsaved changes, asks to save/discard/cancel.
	Returns True if it's fine to proceed with closing or replacing the view
	(nothing unsaved, or the user just saved/discarded), False if the caller
	must abort (user cancelled). Shared by PaneTextView._exit_with_dirty_check
	and begin_new_view(), which otherwise would silently drop unsaved edits
	when a second view replaces the currently open buffer. Also shared by
	non-text views (e.g. PaneImageView, core/imageviewer.py) that have no
	`_editing`/`document()` of their own - getattr's False default short-
	circuits before `document()` is ever called on them, so they always
	report safe to close.
	"""
	if not (getattr(view, '_editing', False) and view.document().isModified()):
		return True
	answer = show_alert('Save changes before closing?', YES | NO | CANCEL, YES)
	if answer & CANCEL:
		return False
	if answer & YES:
		view._save()
	return True

def begin_new_view(pane):
	"""
	Confirms/discards any existing viewer in this pane's widget, then returns
	(widget, bg, fg) for constructing the replacement PaneTextView. Returns
	None if the user cancelled a save/discard prompt for unsaved edits
	already open in this pane, in which case the caller must not replace it.
	Shared by show_text_viewer and show_text_in_viewer (core/textviewer.py).
	"""
	widget = pane._widget
	existing_view = getattr(widget, '_text_view', None)
	if existing_view is not None and not confirm_close(existing_view):
		# User cancelled out of the save/discard prompt for the view
		# currently open in this pane — leave it open, don't replace it.
		return None
	close_view(widget)
	palette = widget._file_view.palette()
	bg = palette.color(QPalette.Base).name()
	fg = palette.color(QPalette.Text).name()
	return widget, bg, fg

def mount_view(pane, widget, view, focus_view=True):
	"""
	Swaps `view` into the pane's layout in place of the (hidden) file list.
	Shared tail of show_text_viewer/show_text_in_viewer once the PaneTextView
	itself has been constructed and its text set.

	focus_view=False mounts the viewer without grabbing keyboard focus — used
	when viewing into the *other* pane (ViewFileInOtherPane), so the pane the
	command ran from stays focused for continued browsing.
	"""
	widget.layout().addWidget(view)
	widget._file_view.setVisible(False)
	widget._text_view = view
	# Re-point the pane's focus proxy at the viewer. switch_panes() ends by
	# calling the *other* pane's focus(), which is setFocus() on this pane's
	# widget — following the proxy. Without this it would land back on the
	# hidden file view instead of the viewer when tabbing back. Set even when
	# not grabbing focus now, so tabbing into this pane later lands on the
	# viewer rather than the hidden file list.
	widget.setFocusProxy(view)
	if focus_view:
		# The command palette's modal dialog restores focus to the (now hidden)
		# file view as it closes, right before this function runs. Grabbing
		# focus here immediately gets clobbered by that restore, so the caret
		# never shows. Defer one event-loop tick so we focus after it settles:
		QTimer.singleShot(0, view.setFocus)
	else:
		# Viewing into the *other* pane: keep focus on the pane the command ran
		# from (the opposite of this target pane) so browsing continues there.
		# Just skipping the setFocus above isn't enough — mounting the viewer
		# still blurs the source pane's file list — so actively re-focus it,
		# on the same deferred tick, to win over that blur.
		panes = pane.window.get_panes()
		source = panes[(panes.index(pane) + 1) % len(panes)]
		QTimer.singleShot(0, source.focus)

@run_in_main_thread
def close_view(pane_widget):
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
