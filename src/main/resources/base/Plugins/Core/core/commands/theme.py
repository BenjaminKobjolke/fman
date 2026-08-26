"""
The appearance commands: "Select theme" picks one of fman's color themes
from the command palette's quicksearch UI, "Set window opacity" makes the
window see-through. Both apply immediately, no restart. The themes
themselves - and everything about how colors and opacity are resolved -
live in the engine (fman.impl.themes); this module is the thin fman-facing
glue. See docs/THEMES.md.
"""
from core.quicksearch_matchers import contains_chars, \
	contains_chars_after_separator
from fman import ApplicationCommand, QuicksearchItem, get_theme, get_themes, \
	get_window_opacity, set_theme, set_window_opacity, show_quicksearch
from itertools import chain

__all__ = ['SelectTheme', 'SetWindowOpacity']

_MATCHERS = (contains_chars_after_separator(' '), contains_chars)

# Shown next to the theme that is currently applied, so the list says which
# one you are looking at without having to remember.
CURRENT_HINT = 'current'

# What the opacity picker offers. Anything between is reachable through the
# set_window_opacity API; these are the steps worth clicking.
OPACITY_PRESETS = (1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7)
# The entry that drops the user's override, so the theme decides again.
THEME_DEFAULT_LABEL = 'Theme default'

def _matched_items(entries, current, query):
	"""
	The quicksearch items for `entries` - (value, label) pairs - best
	matches first, with `current`'s entry marked. Pure (no fman imports
	beyond QuicksearchItem) so it can be tested without a running fman - see
	core/tests/commands/test_theme.py.
	"""
	buckets = [[] for _ in _MATCHERS]
	for value, label in entries:
		for i, matcher in enumerate(_MATCHERS):
			highlight = matcher(label.lower(), query.lower())
			if highlight is not None:
				hint = CURRENT_HINT if value == current else ''
				buckets[i].append(
					QuicksearchItem(value, label, highlight, hint=hint)
				)
				break
	return list(chain.from_iterable(buckets))

def get_theme_items(names, current, query):
	return _matched_items([(name, name) for name in names], current, query)

def _opacity_entries():
	# "Theme default" first: it is the way back, and it is what gets
	# preselected when the current opacity is not one of the presets.
	return [(None, THEME_DEFAULT_LABEL)] + \
		[(value, '%d%%' % round(value * 100)) for value in OPACITY_PRESETS]

def get_opacity_items(current, query):
	return _matched_items(_opacity_entries(), current, query)

class SelectTheme(ApplicationCommand):

	aliases = ('Select theme',)

	def __call__(self):
		names = get_themes()
		current = get_theme()
		# Preselect the active theme, the way SortByColumn preselects the
		# current sort column. The unfiltered list is in `names` order.
		item = names.index(current) if current in names else 0
		result = show_quicksearch(
			lambda query: get_theme_items(names, current, query), item=item
		)
		if result:
			set_theme(result[1])

class SetWindowOpacity(ApplicationCommand):

	aliases = ('Set window opacity',)

	def __call__(self):
		current = get_window_opacity()
		values = [value for value, _ in _opacity_entries()]
		item = values.index(current) if current in values else 0
		result = show_quicksearch(
			lambda query: get_opacity_items(current, query), item=item
		)
		if result:
			set_window_opacity(result[1])
