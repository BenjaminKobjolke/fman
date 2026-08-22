"""
Font-size zoom for the text viewer (core/textviewer.py) - mirrors the pane
font-size feature (core/commands/__init__.py: increase/decrease/reset pane
font size) but applies to the viewer's own QPlainTextEdit, persisted under
its own settings key so the two zoom levels are independent. Split out of
core/textviewer.py to stay under the project's 300-line file cap.

Deliberately decoupled from PyQt widget styling: callers pass an `apply_size`
callback (new size, or None to clear the override) rather than this module
touching stylesheets itself.
"""
from core.font_size import clamp_font_size
from core.key_bindings import get_shortcuts_for_command
from core.settings import get_setting, save_setting
from fman import PLATFORM
from PyQt5.QtGui import QFontInfo

_FALLBACK_VIEW_FONT_SIZE = 11 if PLATFORM == 'Mac' else 9
_SETTING_KEY = 'text_viewer_font_size'

def get_saved_view_font_size():
	return get_setting('Core Settings.json', _SETTING_KEY)

def save_view_font_size(size):
	# size=None clears the override (Reset), falling back to the theme's own
	# font again - mirrors _save_pane_font_size in commands/__init__.py.
	save_setting('Core Settings.json', _SETTING_KEY, size)

def effective_view_font_size(view):
	# Base to step from: whatever font Qt is actually rendering the viewer
	# with right now (theme default, or a previously-applied override).
	size = QFontInfo(view.font()).pointSize()
	return size if size > 0 else _FALLBACK_VIEW_FONT_SIZE

def change_view_font_size(view, apply_size, delta):
	base = get_saved_view_font_size()
	if base is None:
		base = effective_view_font_size(view)
	new_size = clamp_font_size(base, delta)
	save_view_font_size(new_size)
	apply_size(new_size)

def reset_view_font_size(apply_size):
	save_view_font_size(None)
	apply_size(None)

def zoom_delta_for(key_event, key_bindings):
	"""
	Pure (no Qt event, just a QtKeyEvent + parsed Key Bindings.json): +1/-1 if
	`key_event` matches whatever the user currently has increase/decrease
	pane font size bound to (default Alt+Up/Alt+Down, but this must follow a
	rebind), else None. Reuses the pane font-size feature's own shortcut so
	the viewer doesn't invent a second, separate zoom binding.
	"""
	for command, delta in (
		('increase_pane_font_size', +1), ('decrease_pane_font_size', -1)
	):
		shortcuts = get_shortcuts_for_command(key_bindings, command)
		if any(key_event.matches(shortcut) for shortcut in shortcuts):
			return delta
	return None
