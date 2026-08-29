"""
Font-size zoom for the text viewer (core/textviewer.py) - mirrors the pane
font-size feature (core/commands/pane_view.py: increase/decrease/reset pane
font size) but applies to the viewer's own QPlainTextEdit, persisted under
its own settings key so the two zoom levels are independent. Split out of
core/textviewer.py to stay under the project's 300-line file cap.

Deliberately decoupled from PyQt widget styling: callers pass an `apply_size`
callback (new size, or None to clear the override) rather than this module
touching stylesheets itself.
"""
from core.font_size import change_font_size, effective_font_size, 	get_saved_font_size, reset_font_size, save_font_size
from core.key_bindings import format_shortcut_hint, get_shortcuts_for_command

_SETTING_KEY = 'text_viewer_font_size'

def get_saved_view_font_size():
	return get_saved_font_size(_SETTING_KEY)

def save_view_font_size(size):
	save_font_size(_SETTING_KEY, size)

def effective_view_font_size(view):
	return effective_font_size(view.font)

def change_view_font_size(view, apply_size, delta):
	change_font_size(_SETTING_KEY, view.font, apply_size, delta)

def reset_view_font_size(apply_size):
	reset_font_size(_SETTING_KEY, apply_size)

def zoom_actions(view, apply_size, key_bindings):
	"""
	The three ViewerAction tuples the text viewer's palette shows for zoom
	(see core/viewer_navigation.py). Lives here rather than in
	core/textviewer.py both because the labels belong with the zoom they
	drive and because that file is at the 300-line cap. key_bindings is the
	global Key Bindings.json: the two step entries hint at the pane
	font-size shortcut they follow, and Reset ships no key at all.
	"""
	return [
		(
			'Increase font size',
			lambda: change_view_font_size(view, apply_size, +1),
			format_shortcut_hint(
				get_shortcuts_for_command(key_bindings, 'increase_pane_font_size')
			),
		),
		(
			'Decrease font size',
			lambda: change_view_font_size(view, apply_size, -1),
			format_shortcut_hint(
				get_shortcuts_for_command(key_bindings, 'decrease_pane_font_size')
			),
		),
		('Reset font size', lambda: reset_view_font_size(apply_size), ''),
	]

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
