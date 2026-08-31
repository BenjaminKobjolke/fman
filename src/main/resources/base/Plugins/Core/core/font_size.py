"""
Shared font-size zoom for widget zoom features: pane font size
(core/commands/pane_view.py) and the text viewer's own zoom
(core/textviewer.py, driven by core/textviewer_zoom.py). Kept in its own
module (rather than importing one feature from the other) since
the Core command package imports core/textviewer.py at module load
(core/commands/opening.py -> core/viewers.py) - the reverse import would
be circular.

Both features are the same four steps: read the saved override, fall back to
the size the widget is actually rendering with, clamp the step, save and
apply. Only "which settings key" and "how to apply a size to a widget"
differ, so callers pass those in. They used to carry a copy of the algorithm
each, and the copies had already drifted - only the pane one guarded the
font read against a dead widget.
"""
from core.settings import get_setting, save_setting
from fman import PLATFORM
from PyQt5.QtGui import QFontInfo

MIN_FONT_SIZE = 6
MAX_FONT_SIZE = 40
# What to step from when the widget cannot say what it is rendering with.
FALLBACK_FONT_SIZE = 11 if PLATFORM == 'Mac' else 9

_SETTINGS_JSON = 'Core Settings.json'

def clamp_font_size(current, delta):
	return max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, current + delta))

def get_saved_font_size(setting_key):
	return get_setting(_SETTINGS_JSON, setting_key)

def save_font_size(setting_key, size):
	# size=None clears the override (Reset), falling back to the theme's own
	# font again.
	save_setting(_SETTINGS_JSON, setting_key, size)

def effective_font_size(get_font, fallback=FALLBACK_FONT_SIZE):
	# Base to step from: the font the widget is actually rendering with right
	# now (the theme's, or an override applied earlier). get_font is a
	# callable, not a QFont, because reaching the widget can fail - a pane
	# whose Qt object has been deleted raises RuntimeError, and a pane that
	# has no file view yet raises AttributeError.
	try:
		size = QFontInfo(get_font()).pointSize()
	except (AttributeError, RuntimeError):
		return fallback
	return size if size > 0 else fallback

def change_font_size(setting_key, get_font, apply_size, delta):
	# Returns the size it settled on (clamping means that isn't always
	# base + delta), for callers that report it - reading it back off the
	# widget wouldn't work: apply_size sets a stylesheet, which get_font
	# doesn't reflect.
	base = get_saved_font_size(setting_key)
	if base is None:
		base = effective_font_size(get_font)
	new_size = clamp_font_size(base, delta)
	save_font_size(setting_key, new_size)
	apply_size(new_size)
	return new_size

def reset_font_size(setting_key, apply_size):
	save_font_size(setting_key, None)
	apply_size(None)
