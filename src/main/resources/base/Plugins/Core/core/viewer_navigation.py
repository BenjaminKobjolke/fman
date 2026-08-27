"""
Next/previous-file navigation shared by every in-pane viewer - the built-in
three (core/imageviewer.py, core/videoviewer.py, core/textviewer.py) and any a
plugin registers. Rather than listing and sorting the directory itself, it
walks the pane's own cursor (move_cursor_down/up + get_file_under_cursor), so
it inherits the pane's live sort order and filters for free, then re-runs the
"view_file" command to swap in whichever viewer matches the file it landed on.

"Advance only for same type" is a per-viewer toggle persisted in
Core Settings.json via core/settings.py - keeping the image viewer from jumping
into a video and vice-versa. Each viewer owns its own key, derived from its
name (see _same_type_key), defaulting to on.

Also home to the small viewer-scoped command-palette plumbing
(open_viewer_palette) that all three viewers share, so the quicksearch handling
lives in one place rather than being copied into each viewer widget.
"""
from collections import namedtuple
from core.command_keywords import get_keywords
from core.keyword_editor import edit_command_keywords
from core.quicksearch_matchers import bucket_count, contains_chars, \
	match_titles_or_keywords
from core.settings import get_setting, save_setting
from fman import show_quicksearch, show_status_message, QuicksearchItem

_SETTINGS_FILE = 'Core Settings.json'

def _same_type_key(category):
	# Derived rather than tabulated, so a plugin's viewer gets its own setting
	# without touching this file. Reproduces the three keys the built-in
	# viewers have always used ('image_viewer_advance_same_type', ...), so
	# nothing needs migrating.
	#
	# KeyError on an unknown category stays deliberate: callers pass a fixed
	# literal per viewer, so a typo should fail loudly rather than silently
	# reading - and later writing - a bogus key. Deriving alone would not do
	# that, hence the registry check.
	from core.viewers import viewer_for_category
	if viewer_for_category(category) is None:
		raise KeyError(category)
	return '%s_viewer_advance_same_type' % category

def get_same_type_only(category):
	return bool(get_setting(_SETTINGS_FILE, _same_type_key(category), True))

def toggle_same_type_only(category):
	new_value = not get_same_type_only(category)
	save_setting(_SETTINGS_FILE, _same_type_key(category), new_value)
	show_status_message(
		'Advance only for same type: %s' % ('on' if new_value else 'off')
	)
	return new_value

def _category(url):
	# A viewer's name ('image' | 'video' | 'text' | a plugin's own) or None,
	# meaning nothing views this in-pane: a directory, a binary, or a non-local
	# url. Lazy import because core/viewers.py imports the three viewer modules
	# and those import THIS module, so importing it at load time would be
	# circular (same lazy-import reason videoviewer.py defers `import mpv`).
	from core.viewers import viewer_for
	# ponytail: viewer_for sniffs up to 8 KB per text candidate during a scan -
	# fine for normal directories; add a cache only if it ever measurably drags.
	viewer = viewer_for(url)
	return viewer.name if viewer else None

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
		# The ViewerAction tuples shared by all three viewers'
		# _get_actions(). Hints are blank: these ship no default key.
		return [
			('Next file', self.next_file, '', 'viewer_next_file'),
			(
				'Previous file', self.previous_file, '',
				'viewer_previous_file'
			),
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

# A viewer palette entry. command_name is the viewer pseudo-command this entry
# runs (video_mute, viewer_next_file, ... - see docs/KEYBINDINGS.md), and the
# key its hidden search keywords are stored under. Optional, because most
# entries ship none.
ViewerAction = namedtuple('ViewerAction', 'title action hint command_name')
ViewerAction.__new__.__defaults__ = ('',)

# The viewer palettes search a single, short title each, so the global
# palette's word-boundary and any-order matchers would only ever repeat
# what this one already found.
_MATCHERS = (contains_chars,)

def open_viewer_palette(get_actions):
	"""
	The viewer-scoped Ctrl+Shift+P palette handler shared by all three viewers:
	fuzzy-searches over get_actions() - a callable returning ViewerAction-shaped
	tuples - and runs the chosen action. Replaces the identical
	_open_palette/_suggest_actions pair that used to live in each viewer widget.
	"""
	def suggest(query):
		# One list per rank the matcher helper can return, concatenated -
		# same ranking as the global palette.
		buckets = [[] for _ in range(bucket_count(_MATCHERS))]
		for entry in get_actions():
			entry = ViewerAction(*entry)
			match = match_titles_or_keywords(
				_MATCHERS, [entry.title.lower()],
				get_keywords(entry.command_name), query.lower()
			)
			if match is None:
				continue
			bucket, _index, highlight = match
			# The whole entry as the value, not just its action: Shift+Enter
			# needs the command name and title to edit the entry's keywords.
			buckets[bucket].append(QuicksearchItem(
				entry, entry.title, highlight, entry.hint
			))
		return sum(buckets, [])
	# A loop for the same reason as the global palette's: after editing an
	# entry's keywords, reopen the palette instead of closing it.
	while True:
		result = show_quicksearch(suggest, alt_accept=True)
		if not result:
			return
		_query, entry, alt = result
		if not entry:
			return
		if not alt:
			entry.action()
			return
		edit_command_keywords(entry.command_name, entry.title)

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
