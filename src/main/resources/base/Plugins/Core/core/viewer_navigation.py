"""
Next/previous-file navigation shared by the three in-pane viewers
(core/imageviewer.py, core/videoviewer.py, core/textviewer.py). Rather than
listing and sorting the directory itself, it walks the pane's own cursor
(move_cursor_down/up + get_file_under_cursor), so it inherits the pane's live
sort order and filters for free, then re-runs the "view_file" command to swap in
whichever viewer matches the file it landed on.

"Advance only for same type" is a per-viewer toggle persisted in
Core Settings.json via core/settings.py - keeping the image viewer from jumping
into a video and vice-versa. Each viewer owns its own key (see _SAME_TYPE_KEYS),
defaulting to on.

Also home to the small viewer-scoped command-palette plumbing
(open_viewer_palette) that all three viewers share, so the quicksearch handling
lives in one place rather than being copied into each viewer widget.
"""
from core.quicksearch_matchers import contains_chars
from core.settings import get_setting, save_setting
from fman import show_quicksearch, show_status_message, QuicksearchItem
from fman.url import as_human_readable, splitscheme

_SETTINGS_FILE = 'Core Settings.json'

_SAME_TYPE_KEYS = {
	'image': 'image_viewer_advance_same_type',
	'video': 'video_viewer_advance_same_type',
	'text': 'text_viewer_advance_same_type',
}

def get_same_type_only(category):
	# KeyError on an unknown category is deliberate: callers pass a fixed
	# literal per viewer, so a typo should fail loudly rather than silently
	# reading a bogus key.
	return bool(get_setting(_SETTINGS_FILE, _SAME_TYPE_KEYS[category], True))

def toggle_same_type_only(category):
	new_value = not get_same_type_only(category)
	save_setting(_SETTINGS_FILE, _SAME_TYPE_KEYS[category], new_value)
	show_status_message(
		'Advance only for same type: %s' % ('on' if new_value else 'off')
	)
	return new_value

def _category(url):
	# 'image' | 'video' | 'text' | None (None = not viewable in-pane: a
	# directory, a binary, or a non-local url). Lazy imports because the three
	# viewer modules import THIS module, so importing them at load time would be
	# circular (same lazy-import reason videoviewer.py defers `import mpv`).
	from core.imageviewer import is_image
	from core.videoviewer import is_video
	from core.textviewer_io import is_text_file
	from fman.fs import is_dir
	if splitscheme(url)[0] != 'file://':
		return None
	if is_image(url):
		return 'image'
	if is_video(url):
		return 'video'
	if is_dir(url):
		# Guard before is_text_file, which would try to read the directory.
		return None
	# ponytail: is_text_file sniffs up to 8 KB per candidate during a scan -
	# fine for normal directories; add a cache only if it ever measurably drags.
	if is_text_file(as_human_readable(url)):
		return 'text'
	return None

class ViewerNavigator:
	"""
	Per-viewer navigation collaborator, injected into each viewer widget so the
	next/previous-file and same-type-toggle wiring lives in one place instead of
	being duplicated across imageviewer/videoviewer/textviewer. Bound once to a
	pane and the owning viewer's category ('image'|'video'|'text').
	"""
	def __init__(self, pane, category):
		self._pane = pane
		self._category = category

	def next_file(self):
		advance(self._pane, +1, self._category)

	def previous_file(self):
		advance(self._pane, -1, self._category)

	def toggle_same_type(self):
		toggle_same_type_only(self._category)

	def same_type_label(self):
		# Label reflects the action the entry performs, like the text viewer's
		# auto-reload label: when the restriction is on, the entry lifts it.
		if get_same_type_only(self._category):
			return 'Advance across all file types'
		return 'Advance only for same type'

	def actions(self):
		# The (title, callable, hint) palette tuples shared by all three
		# viewers' _get_actions(). Hints are blank: these ship no default key.
		return [
			('Next file', self.next_file, ''),
			('Previous file', self.previous_file, ''),
			(self.same_type_label(), self.toggle_same_type, ''),
		]

	def commands(self):
		# The bindable-pseudo-command mappings each viewer merges into its own
		# _bindable_commands() dict, kept here so the navigation contract lives
		# in one place (see docs/KEYBINDINGS.md for the command names).
		return {
			'viewer_next_file': self.next_file,
			'viewer_previous_file': self.previous_file,
			'viewer_toggle_same_type_advance': self.toggle_same_type,
		}

def open_viewer_palette(get_actions):
	"""
	The viewer-scoped Ctrl+Shift+P palette handler shared by all three viewers:
	fuzzy-searches over get_actions() - a callable returning (title, action,
	hint) tuples - and runs the chosen action. Replaces the identical
	_open_palette/_suggest_actions pair that used to live in each viewer widget.
	"""
	def suggest(query):
		for title, action, hint in get_actions():
			highlight = contains_chars(title.lower(), query.lower())
			if highlight is not None:
				yield QuicksearchItem(action, title, highlight, hint)
	result = show_quicksearch(suggest)
	if result:
		_query, action = result
		if action:
			action()

def advance(pane, direction, category):
	"""
	Step the pane cursor by `direction` (+1 next, -1 previous) to the nearest
	viewable file, skipping non-viewable entries and - when this viewer's
	same-type toggle is on - files of a different category, then re-run
	view_file on it. Restores the cursor and shows a status message if there is
	no such file in that direction.
	"""
	same_type_only = get_same_type_only(category)
	start = pane.get_file_under_cursor()
	step = pane.move_cursor_down if direction > 0 else pane.move_cursor_up
	while True:
		before = pane.get_file_under_cursor()
		step()
		after = pane.get_file_under_cursor()
		if not after or after == before:
			# Qt's moveCursor clamps at the ends (no wrap), so an unchanged
			# cursor means we hit the boundary without finding a match.
			pane.place_cursor_at(start)
			show_status_message('No further file to view')
			return
		found = _category(after)
		if found is None:
			continue
		if same_type_only and found != category:
			continue
		pane.run_command('view_file')
		return
