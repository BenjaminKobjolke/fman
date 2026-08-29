"""
The common "get/set one key in a JSON settings file, None clears the key"
pattern - used by both the pane font-size feature
(core/commands/pane_view.py: pane_font_size in Core Settings.json) and the
text viewer's own font-size feature (core/textviewer_zoom.py:
text_viewer_font_size in Core Settings.json).
"""
from fman import load_json, save_json

def get_setting(json_name, key, default=None):
	return load_json(json_name, default={}).get(key, default)

def save_setting(json_name, key, value):
	# value=None clears the key (falls back to whatever default the caller
	# uses when the key is absent) instead of writing a hard-coded default.
	settings = load_json(json_name, default={})
	if value is None:
		settings.pop(key, None)
	else:
		settings[key] = value
	save_json(json_name)
