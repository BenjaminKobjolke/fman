"""
Color themes: the single source of truth for every color in fman's UI.

fman's look used to be spread over three places that could drift apart -
the hardcoded hex literals in resources/base/styles.qss, the QPalette built
in application_context.py, and the quicksearch item colors in
Plugins/Core/Theme.css. This module replaces all three with one flat map of
named color tokens:

  * styles.qss and Theme.css now contain `$token` placeholders which
    Theme (impl/theme.py) substitutes at load time and again on every theme
    switch.
  * build_palette(...) & co. derive the QPalette from the *same* tokens, so
    a theme cannot style the file list one way and the text viewer - which
    samples QPalette.Base - another.

A theme is one JSON file listing only the tokens it changes; everything else
falls back to DEFAULT_COLORS, which holds exactly the values fman shipped
before themes existed. That is what makes the default theme provably
identical to the old look: its file is empty.

See docs/THEMES.md for the token reference and how to add a theme.
"""
from fman.impl.util.qt.thread import run_in_main_thread
from glob import glob
from os.path import basename, join, splitext
from PyQt5.QtGui import QColor, QPalette
from string import Template

import json

# The theme used when the user has not picked one. Its JSON file is empty:
# DEFAULT_COLORS *is* Monokai.
DEFAULT_THEME = 'Monokai'

# The setting key in %APPDATA%/fman/Local/Settings.json. It lives there and
# not in Core Settings.json because the palette is built before any plugin
# (and thus fman.load_json) is available - see ApplicationContext.app.
THEME_SETTING = 'theme'

# The user's own window opacity, in the same file and for the same reason.
# It overrides whatever the active theme asks for; absent means "follow the
# theme". Below MIN_OPACITY the window is too faint to work in.
OPACITY_SETTING = 'window_opacity'
DEFAULT_OPACITY = 1.0
MIN_OPACITY = 0.3

# Every color fman draws, with the values it used before themes existed.
# A token appears here iff it is referenced from styles.qss, Theme.css or
# one of the build_*palette functions below - test_themes.py enforces both
# directions, so a hex literal cannot creep back into the stylesheets.
DEFAULT_COLORS = {
	# File list
	'pane_bg': '#272822',
	'pane_fg': '#75715e',
	'pane_fg_dir': 'white',
	'pane_selected_fg': '#f92672',
	'pane_cursor_bg': '#49483e',
	'header_bg': '#363731',
	# Text
	'muted_fg': '#8f908a',
	'bright_fg': 'white',
	'readonly_fg': '#9a9a9a',
	# Chrome
	'border': '#7d7d7d',
	'input_bg': '#303030',
	'input_border': '#363731',
	'statusbar_bg_top': '#5b5b5b',
	'statusbar_bg_bottom': '#545454',
	'locationbar_border': '#262626',
	# Quicksearch popup
	'popup_bg': '#404040',
	'popup_selected_bg': '#575757',
	'popup_query_border': '#8e8e8e',
	'popup_query_inner_border': '#2c2c2c',
	'popup_input_bg': '#e6e6e6',
	'popup_input_fg': '#1d1d1d',
	'popup_input_border': '#dddddd',
	'popup_input_border_top': '#aeaeae',
	'popup_input_border_left': '#c9c9c9',
	'popup_input_border_right': '#d0d0d0',
	'popup_item_fg': '#c8c8c8',
	'popup_divider_top': '#4d4d4d',
	'popup_divider_bottom': '#363636',
	# QPalette-only: roles Qt draws itself, which no stylesheet reaches.
	'window_bg': '#2b2b2b',
	'main_window_bg': '#444444',
	'base_bg': '#131313',
	'alt_row_bg': '#42403b',
	'button_bg': '#292929',
	'button_fg': '#b6b3ab',
	'palette_midlight': '#333333',
	'palette_mid': '#252525',
	'palette_dark': '#202020',
	'palette_shadow': '#1d1d1d'
}

def substitute(text, colors):
	"""
	Replaces $token placeholders in a QSS/CSS file's text. safe_substitute
	leaves unknown names and stray '$' untouched, so a user's own Theme.css
	can never fail to load because of a dollar sign.
	"""
	return Template(text).safe_substitute(colors)

# A theme only has to name the ~15 tokens that have no entry here; every
# other token inherits from its parent unless the theme overrides it. That
# is what keeps "write a theme" at fifteen colors instead of thirty-seven,
# and it is why `base_bg` follows `pane_bg`: a new theme cannot accidentally
# leave the text viewer (which samples QPalette.Base) on the old background.
FALLBACKS = {
	'pane_fg_dir': 'bright_fg',
	'readonly_fg': 'muted_fg',
	'input_border': 'header_bg',
	'statusbar_bg_bottom': 'statusbar_bg_top',
	'locationbar_border': 'header_bg',
	'popup_query_border': 'border',
	# These inherit `border`, never `popup_bg`: a separator that defaults to
	# the surface it sits on is invisible by construction, which turns the
	# command palette into an undifferentiated wall of text.
	'popup_query_inner_border': 'border',
	'popup_divider_top': 'border',
	'popup_divider_bottom': 'border',
	'popup_input_bg': 'input_bg',
	'popup_input_fg': 'bright_fg',
	'popup_input_border': 'border',
	'popup_input_border_top': 'popup_input_border',
	'popup_input_border_left': 'popup_input_border',
	'popup_input_border_right': 'popup_input_border',
	'base_bg': 'pane_bg',
	'main_window_bg': 'window_bg',
	'alt_row_bg': 'pane_cursor_bg',
	'button_bg': 'window_bg',
	'button_fg': 'muted_fg',
	'palette_midlight': 'header_bg',
	'palette_mid': 'button_bg',
	'palette_dark': 'button_bg',
	'palette_shadow': 'button_bg'
}

# A color value ends up inside a QSS declaration, so anything that could
# close it turns a theme file into a stylesheet injection:
_ILLEGAL_IN_COLOR = set(';{}\n\r')

def is_valid_color(value):
	return isinstance(value, str) \
		and not _ILLEGAL_IN_COLOR & set(value) \
		and QColor(value).isValid()

def resolve_colors(theme_json):
	"""
	A theme's partial color map turned into a value for every token, via
	FALLBACKS and then DEFAULT_COLORS. Unknown tokens and invalid values are
	ignored rather than raising - a typo in a theme file must not stop fman
	from starting.
	"""
	given = {
		key: value for key, value in (theme_json.get('colors') or {}).items()
		if key in DEFAULT_COLORS and is_valid_color(value)
	}
	return {token: _resolve(token, given) for token in DEFAULT_COLORS}

def _resolve(token, given):
	# Inherit from the nearest ancestor the theme actually named. If it
	# named none of them, the token keeps its own default rather than the
	# ancestor's - otherwise an empty theme would not reproduce
	# DEFAULT_COLORS, which is what makes the default look provable.
	node = token
	seen = set()
	while node is not None and node not in seen:
		if node in given:
			return given[node]
		seen.add(node)
		node = FALLBACKS.get(node)
	return DEFAULT_COLORS[token]

def list_themes(dirs):
	"""
	Theme names available in `dirs`, sorted. A theme's name is its file name
	without the extension - the same string that is shown in the command
	palette and stored in the settings, so there is no second place for it
	to disagree with.
	"""
	# The default is always offered: it needs no file (an empty JSON is
	# what it is) and must stay reachable even if `dirs` are missing.
	result = {DEFAULT_THEME}
	for dir_ in dirs:
		for path in glob(join(dir_, '*.json')):
			result.add(splitext(basename(path))[0])
	return sorted(result)

def _read_theme_json(name, dirs):
	"""
	Theme `name`'s JSON object, or {} if it does not exist or is unreadable.
	Later dirs win, so a user theme shadows a bundled one of the same name.
	Never raises: a broken theme file must not stop fman from starting.
	"""
	result = {}
	for dir_ in dirs:
		try:
			with open(join(dir_, name + '.json'), 'r') as f:
				contents = json.load(f)
		except (OSError, ValueError):
			continue
		# A theme file is valid JSON without being an object: `[]` and `5`
		# parse fine and would make every .get(...) below raise. Ignore such
		# a file the way an unreadable one is ignored.
		if isinstance(contents, dict):
			result = contents
	return result

def load_theme(name, dirs):
	"""
	The colors of theme `name`, or DEFAULT_COLORS if it does not exist or is
	unreadable.
	"""
	return resolve_colors(_read_theme_json(name, dirs))

def load_opacity(name, dirs):
	"""
	The window opacity theme `name` asks for, or None if it asks for none.
	It lives beside "colors" rather than in it because it is not a color:
	resolve_colors drops every value that is not a valid QColor.
	"""
	return _normalize_opacity(_read_theme_json(name, dirs).get('opacity'))

def _normalize_opacity(value):
	"""
	`value` as a float in [MIN_OPACITY, 1.0], or None if it is not a usable
	opacity. Shared by the theme files and the user's own setting so both
	answer to one contract. Booleans are rejected explicitly: True is an int
	in Python and would otherwise read as "fully opaque".
	"""
	if isinstance(value, bool) or not isinstance(value, (int, float)):
		return None
	result = float(value)
	return result if MIN_OPACITY <= result <= DEFAULT_OPACITY else None

def build_palette(colors):
	result = QPalette()
	result.setColor(QPalette.Window, QColor(colors['window_bg']))
	result.setColor(QPalette.WindowText, QColor(colors['bright_fg']))
	result.setColor(QPalette.Base, QColor(colors['base_bg']))
	result.setColor(QPalette.AlternateBase, QColor(colors['alt_row_bg']))
	result.setColor(QPalette.ToolTipBase, QColor(colors['base_bg']))
	result.setColor(QPalette.ToolTipText, QColor(colors['bright_fg']))
	# Qt draws the focus rectangle (view/__init__.py) in the Light role, so
	# it tracks the cursor row's background by definition:
	result.setColor(QPalette.Light, QColor(colors['pane_cursor_bg']))
	result.setColor(QPalette.Midlight, QColor(colors['palette_midlight']))
	result.setColor(QPalette.Button, QColor(colors['button_bg']))
	result.setColor(QPalette.Mid, QColor(colors['palette_mid']))
	result.setColor(QPalette.Dark, QColor(colors['palette_dark']))
	result.setColor(QPalette.Shadow, QColor(colors['palette_shadow']))
	result.setColor(QPalette.Text, QColor(colors['bright_fg']))
	result.setColor(QPalette.ButtonText, QColor(colors['button_fg']))
	result.setColor(QPalette.Link, QColor(colors['bright_fg']))
	result.setColor(QPalette.LinkVisited, QColor(colors['bright_fg']))
	# Prevent blue highlight around buttons when the window (/dialog) is in
	# the background and thus inactive:
	result.setColor(
		QPalette.Inactive, QPalette.Highlight,
		result.color(QPalette.Midlight)
	)
	return result

def build_main_window_palette(colors):
	result = QPalette(build_palette(colors))
	result.setColor(QPalette.Window, QColor(colors['main_window_bg']))
	return result

def build_progress_bar_palette(colors):
	result = QPalette(build_main_window_palette(colors))
	# On Windows, when the progress bar (/the progress dialog) is in the
	# background, ie. not the active window, its color changes from blue to
	# white. Avoid this:
	result.setColor(
		QPalette.Inactive, QPalette.Highlight,
		result.color(QPalette.Active, QPalette.Highlight)
	)
	return result

class ThemeController:

	"""
	Reads and switches the active theme. Takes the ApplicationContext rather
	than its five collaborators separately: everything a theme switch has to
	touch (the QApplication, the Theme, the main window, the settings file
	and the theme directories) already hangs off it, and the alternative is
	a five-argument constructor that has to be kept in sync with it anyway.
	"""

	def __init__(self, app_context):
		self._ctxt = app_context

	def get_themes(self):
		return list_themes(self._ctxt.theme_dirs)

	def get_theme(self):
		return self._ctxt.local_settings.get(THEME_SETTING, DEFAULT_THEME)

	def set_theme(self, name):
		colors = load_theme(name, self._ctxt.theme_dirs)
		# Resolve the opacity for the *incoming* theme and pass it in: the
		# new name is only saved below, so _apply cannot look it up itself.
		self._apply(colors, self._get_opacity(name))
		settings = self._ctxt.local_settings
		settings[THEME_SETTING] = name
		settings.flush()

	def get_opacity(self):
		return self._get_opacity(self.get_theme())

	def set_opacity(self, value):
		"""
		Applies `value` and remembers it across restarts. value=None drops
		the override, so the active theme's opacity applies again - the same
		"None clears the key" rule the plugin settings use. Raises ValueError
		for a number fman cannot use.
		"""
		if value is not None and _normalize_opacity(value) is None:
			raise ValueError(
				'Opacity must be a number between %s and %s, not %r'
				% (MIN_OPACITY, DEFAULT_OPACITY, value)
			)
		settings = self._ctxt.local_settings
		if value is None:
			settings.pop(OPACITY_SETTING)
		else:
			settings[OPACITY_SETTING] = float(value)
		settings.flush()
		self._apply_opacity(self.get_opacity())

	def _get_opacity(self, theme_name):
		# One precedence chain, parameterized by theme name so set_theme can
		# ask it about a theme that is not the saved one yet: the user's own
		# setting wins, then what the theme asks for, then fully opaque.
		# Never reads main_window.windowOpacity(): the window does not exist
		# yet when this first runs, and Qt quantizes opacity to 1/255, so a
		# value read back never equals the one that was set.
		saved = _normalize_opacity(
			self._ctxt.local_settings.get(OPACITY_SETTING, None)
		)
		if saved is not None:
			return saved
		from_theme = load_opacity(theme_name, self._ctxt.theme_dirs)
		return DEFAULT_OPACITY if from_theme is None else from_theme

	@run_in_main_thread
	def _apply_opacity(self, opacity):
		self._ctxt.main_window.setWindowOpacity(opacity)

	@run_in_main_thread
	def _apply(self, colors, opacity):
		# Commands run off the main thread (see PaneCommandRegistry), and
		# touching QPalettes from there is not allowed.
		#
		# Palette first, style sheet second: QApplication.setStyleSheet
		# re-polishes every widget, which is what makes the new palette
		# actually repaint. The other order leaves stale colors behind.
		self._ctxt.app.setPalette(build_palette(colors))
		main_window = self._ctxt.main_window
		main_window.setPalette(build_main_window_palette(colors))
		# Re-read for each new ProgressDialog (widgets.py), so the next one
		# picks the new colors up without restarting fman:
		main_window.set_progress_bar_palette(
			build_progress_bar_palette(colors)
		)
		# A theme may ask for an opacity too, so switching theme has to move
		# it - back to opaque included, when the new theme asks for nothing.
		main_window.setWindowOpacity(opacity)
		self._ctxt.theme.set_colors(colors)
