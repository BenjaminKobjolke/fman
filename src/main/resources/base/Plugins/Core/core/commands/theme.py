"""
The appearance commands: "Select theme" picks one of fman's color themes
from the command palette's quicksearch UI, "Select icon set" picks which
icons the file list draws, "Set icon size" how big, "Set icon color" what
color, "Select font" which font family the UI is drawn in, "Reset font"
hands that choice back to the theme, and "Set window opacity" makes the
window see-through. All apply immediately, no restart. The themes
themselves - and everything about how colors, opacity, icons, their size
and color, and the font are resolved - live in the engine
(fman.impl.themes); this module is the thin fman-facing glue.
See docs/THEMES.md.
"""
from core.panes import reload_panes
from core.quicksearch_matchers import contains_chars, \
	contains_chars_after_separator, matched_in_order
from fman import ApplicationCommand, QuicksearchItem, get_font, \
	get_fonts, get_icon_color, get_icon_set, get_icon_sets, \
	get_icon_size, get_theme, get_themes, get_window_opacity, set_font, \
	set_icon_color, set_icon_set, set_icon_size, set_theme, \
	set_window_opacity, show_quicksearch

__all__ = [
	'ResetFont', 'SelectFont', 'SelectIconSet', 'SelectTheme',
	'SetIconColor', 'SetIconSize', 'SetWindowOpacity'
]

_MATCHERS = (contains_chars_after_separator(' '), contains_chars)

# Shown next to the theme that is currently applied, so the list says which
# one you are looking at without having to remember.
CURRENT_HINT = 'current'

# What the opacity picker offers. Anything between is reachable through the
# set_window_opacity API; these are the steps worth clicking.
OPACITY_PRESETS = (1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7)
# Likewise for icon size, in pixels. 16 is what Qt draws without being asked.
ICON_SIZE_PRESETS = (16, 20, 24, 32, 48)
# And for the icon color. Any color Qt understands works through the
# set_icon_color API; these are the ones worth clicking, named because a hex
# code is not something to pick from a list. Order is the list's order.
ICON_COLOR_NAMES = (
	('#00ff41', 'Green'),
	('#00e5ff', 'Cyan'),
	('#4fa3ff', 'Blue'),
	('#ffb300', 'Amber'),
	('#ff5252', 'Red'),
	('#ff4fd8', 'Magenta'),
	('#e8e8e8', 'White'),
	('#9e9e9e', 'Grey')
)
ICON_COLOR_PRESETS = tuple(value for value, _ in ICON_COLOR_NAMES)
# The entry that drops the user's override, so the theme decides again.
THEME_DEFAULT_LABEL = 'Theme default'

def _matched_items(entries, current, query):
	"""
	The quicksearch items for `entries` - (value, label) pairs - best
	matches first, with `current`'s entry marked. Pure (no fman imports
	beyond QuicksearchItem) so it can be tested without a running fman - see
	core/tests/commands/test_theme.py.
	"""
	return matched_in_order(
		_MATCHERS, [(label, value) for value, label in entries], query,
		lambda value, label, highlight: QuicksearchItem(
			value, label, highlight,
			hint=CURRENT_HINT if value == current else ''
		)
	)

def get_theme_items(names, current, query):
	return _matched_items(_name_entries(names), current, query)

def get_icon_set_items(names, current, query):
	# No "Theme default" entry: unlike opacity and icon size, every icon set
	# has a name of its own, and "System" already *is* the way back.
	return _matched_items(_name_entries(names), current, query)

def get_font_items(names, current, query):
	# Unlike an icon set, a font has no name that means "stop
	# overriding" - every family is just a family - so the way back is a
	# "Theme default" entry, the way opacity and icon size do it.
	return _matched_items(_font_entries(names), current, query)

def _font_entries(names):
	return _preset_entries(names, lambda name: name)

def _name_entries(names):
	return [(name, name) for name in names]

def _preset_entries(presets, label):
	# "Theme default" first: it is the way back, and it is what gets
	# preselected when the current value is not one of the presets.
	return [(None, THEME_DEFAULT_LABEL)] + \
		[(value, label(value)) for value in presets]

def _opacity_entries():
	return _preset_entries(OPACITY_PRESETS, lambda v: '%d%%' % round(v * 100))

def _icon_size_entries():
	return _preset_entries(ICON_SIZE_PRESETS, lambda v: '%d px' % v)

def _icon_color_entries():
	# The color a theme file would write is the hex, so that is the value;
	# the name is only what the list shows, which is why it is a lookup
	# rather than something derived from the value.
	names = dict(ICON_COLOR_NAMES)
	return _preset_entries(ICON_COLOR_PRESETS, lambda v: names[v])

def get_opacity_items(current, query):
	return _matched_items(_opacity_entries(), current, query)

def get_icon_size_items(current, query):
	return _matched_items(_icon_size_entries(), current, query)

def get_icon_color_items(current, query):
	return _matched_items(_icon_color_entries(), current, query)

def _pick(entries, current, get_items, apply_value):
	"""
	The shape every command in this module has: show the quicksearch with
	the active value preselected, and apply whatever comes back. Factored
	out because the four of them differ only in those three arguments.
	"""
	values = [value for value, _ in entries]
	item = values.index(current) if current in values else 0
	result = show_quicksearch(
		lambda query: get_items(current, query), item=item
	)
	if result:
		apply_value(result[1])

class SelectTheme(ApplicationCommand):

	aliases = ('Select theme',)

	def __call__(self):
		# Preselect the active theme, the way SortByColumn preselects the
		# current sort column. The unfiltered list is in `names` order.
		names = get_themes()
		def apply_theme(name):
			set_theme(name)
			# A theme may carry an icon set, so switching one can change
			# every icon in the panes.
			reload_panes(self.window)
		_pick(
			_name_entries(names), get_theme(),
			lambda current, query: get_theme_items(names, current, query),
			apply_theme
		)

class SelectIconSet(ApplicationCommand):

	aliases = ('Select icon set',)

	def __call__(self):
		names = get_icon_sets()
		def apply_icon_set(name):
			set_icon_set(name)
			reload_panes(self.window)
		_pick(
			_name_entries(names), get_icon_set(),
			lambda current, query: get_icon_set_items(names, current, query),
			apply_icon_set
		)

class SetIconSize(ApplicationCommand):

	aliases = ('Set icon size',)

	def __call__(self):
		# No pane reload: the icons themselves do not change, only how big
		# the view draws them, and setIconSize repaints on its own.
		_pick(
			_icon_size_entries(), get_icon_size(), get_icon_size_items,
			set_icon_size
		)

class SetIconColor(ApplicationCommand):

	aliases = ('Set icon color',)

	def __call__(self):
		# Reloads the panes, unlike SetIconSize: a color changes the icons
		# themselves, so the ones the panes are holding are the old ones.
		def apply_icon_color(color):
			set_icon_color(color)
			reload_panes(self.window)
		_pick(
			_icon_color_entries(), get_icon_color(), get_icon_color_items,
			apply_icon_color
		)

class SelectFont(ApplicationCommand):

	aliases = ('Select font',)

	def __call__(self):
		# No pane reload: a font family is a stylesheet token, and the
		# restyle Theme.set_tokens triggers repaints everything already.
		# (SelectTheme and SetIconColor reload because icons are image
		# files the panes are still holding.)
		names = get_fonts()
		_pick(
			_font_entries(names), get_font(),
			lambda current, query: get_font_items(names, current, query),
			set_font
		)

class ResetFont(ApplicationCommand):

	# The same thing as picking "Theme default" in Select font, but
	# without opening a picker that lists every family on the machine -
	# which is what made the way back hard to find. Palette-only, like
	# ResetPaneFontSize.
	aliases = ('Reset font',)

	def __call__(self):
		set_font(None)

class SetWindowOpacity(ApplicationCommand):

	aliases = ('Set window opacity',)

	def __call__(self):
		_pick(
			_opacity_entries(), get_window_opacity(), get_opacity_items,
			set_window_opacity
		)
