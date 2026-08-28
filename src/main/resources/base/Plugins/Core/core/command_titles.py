"""
User-chosen labels for command palette entries: rename "Quit" to "Exit" and
the row reads Exit. Stored in a user-editable data file next to
Command Keywords.json, keyed by command name - see
docs/COMMAND_PALETTE_KEYWORDS.md.

A rename replaces what the row displays, so the original names are folded into
the command's search keywords: after renaming Quit, typing 'quit' must still
find it.
"""
from core.settings import get_setting

# Same key namespace as Command Keywords.json: command names, viewer
# pseudo-commands included, so both palettes read the one file. fman merges it
# across plugin dirs key by key, so a user file only renames what it names.
COMMAND_TITLES_FILE = 'Command Titles.json'

def get_custom_title(command_name):
	"""
	The user's own label for `command_name`, or '' if there is none. The file
	is user-editable, so a wrong shape is ignored instead of raising inside
	the palette's per-keystroke callback.
	"""
	if not command_name:
		return ''
	title = get_setting(COMMAND_TITLES_FILE, command_name, '')
	if not isinstance(title, str):
		return ''
	return title.strip()

def apply_custom_title(command_name, titles, keywords):
	"""
	`(titles, keywords)` with the user's rename applied: the custom label
	becomes the only displayed title, and the original titles join the
	keywords - lowercased, the way keywords are matched - so the command stays
	findable under its real name. Both are returned unchanged when there is no
	rename.
	"""
	custom_title = get_custom_title(command_name)
	if not custom_title:
		return titles, keywords
	return [custom_title], tuple(keywords) + tuple(
		title.lower() for title in titles
	)
