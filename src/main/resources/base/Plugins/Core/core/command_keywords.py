"""
Hidden search terms for the command palettes. A command is findable by words
that are not in its name - 'transparency' finds "Set window opacity" - without
those words ever being displayed. They live in a user-editable data file
rather than in the code, so anyone can add their own vocabulary; see
docs/COMMAND_PALLETTE.md.
"""
from core.settings import get_setting

# Keys are command names, the same ones Key Bindings.json and Viewer Key
# Bindings.json use (viewer pseudo-commands like video_mute included), so the
# global and the viewer palettes read the one file. fman merges it across
# plugin dirs key by key, so a user file only replaces the commands it names.
COMMAND_KEYWORDS_FILE = 'Command Keywords.json'

def get_keywords(command_name):
	"""
	The hidden search terms for `command_name`, lowercased. The file is
	user-editable, so a wrong shape is ignored instead of raising inside the
	palette's per-keystroke callback.
	"""
	if not command_name:
		return ()
	keywords = get_setting(COMMAND_KEYWORDS_FILE, command_name, ())
	if not isinstance(keywords, list):
		return ()
	return tuple(
		keyword.lower() for keyword in keywords if isinstance(keyword, str)
	)
