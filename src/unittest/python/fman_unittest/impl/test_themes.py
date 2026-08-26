from fman.impl.themes import DEFAULT_COLORS, DEFAULT_THEME, FALLBACKS, \
	MIN_OPACITY, build_main_window_palette, build_palette, \
	build_progress_bar_palette, is_valid_color, list_themes, load_opacity, \
	load_theme, resolve_colors, substitute
from os.path import dirname, exists, join
from PyQt5.QtGui import QColor, QPalette
from tempfile import TemporaryDirectory
from unittest import TestCase

import json
import re

_PROJECT_DIR = dirname(dirname(dirname(dirname(dirname(dirname(
	__file__
))))))
_RESOURCES = join(_PROJECT_DIR, 'src', 'main', 'resources')
_THEMES_DIR = join(_RESOURCES, 'base', 'Themes')
# The two files whose colors the themes own. Any other .qss stays literal on
# purpose - see docs/THEMES.md ("Not themed").
_TEMPLATES = (
	join(_RESOURCES, 'base', 'styles.qss'),
	join(_RESOURCES, 'base', 'Plugins', 'Core', 'Theme.css')
)

_COLOR_LITERAL = re.compile(r'#[0-9a-fA-F]{3,8}\b|\b(?:white|black)\b')
_PLACEHOLDER = re.compile(r'\$([_a-zA-Z][_a-zA-Z0-9]*)')

def _read(path):
	with open(path, 'r', encoding='utf-8') as f:
		return f.read()

class SubstituteTest(TestCase):
	def test_replaces_known_tokens(self):
		self.assertEqual(
			'color: #123456;', substitute('color: $foo;', {'foo': '#123456'})
		)
	def test_leaves_unknown_token(self):
		# safe_substitute, so a user's own Theme.css can contain a '$'
		# without failing to load.
		self.assertEqual('a $b c', substitute('a $b c', {'foo': 'x'}))
	def test_leaves_stray_dollar(self):
		self.assertEqual('100$ ', substitute('100$ ', {'foo': 'x'}))

class ResolveColorsTest(TestCase):
	def test_empty_theme_is_the_default(self):
		self.assertEqual(DEFAULT_COLORS, resolve_colors({}))
	def test_overrides_only_what_it_names(self):
		result = resolve_colors({'colors': {'pane_fg': '#abcdef'}})
		self.assertEqual('#abcdef', result['pane_fg'])
		self.assertEqual(DEFAULT_COLORS['pane_bg'], result['pane_bg'])
	def test_fallback_inherits_from_parent(self):
		# base_bg follows pane_bg, so a theme cannot leave the text viewer
		# on the previous theme's background.
		result = resolve_colors({'colors': {'pane_bg': '#101010'}})
		self.assertEqual('#101010', result['base_bg'])
	def test_fallback_chain(self):
		# border -> popup_input_border -> popup_input_border_top
		result = resolve_colors({'colors': {'border': '#111111'}})
		self.assertEqual('#111111', result['popup_input_border_top'])
	def test_explicit_value_beats_fallback(self):
		result = resolve_colors(
			{'colors': {'pane_bg': '#101010', 'base_bg': '#202020'}}
		)
		self.assertEqual('#202020', result['base_bg'])
	def test_ignores_unknown_token(self):
		self.assertEqual(DEFAULT_COLORS, resolve_colors({'colors': {'nope': 'red'}}))
	def test_ignores_invalid_value(self):
		result = resolve_colors({'colors': {'pane_bg': 'red; } * { color: red'}})
		self.assertEqual(DEFAULT_COLORS['pane_bg'], result['pane_bg'])
	def test_fallback_parents_are_known_tokens(self):
		for token, parent in FALLBACKS.items():
			self.assertIn(token, DEFAULT_COLORS)
			self.assertIn(parent, DEFAULT_COLORS)

class IsValidColorTest(TestCase):
	def test_accepts_hex_and_name(self):
		self.assertTrue(is_valid_color('#ff0000'))
		self.assertTrue(is_valid_color('white'))
	def test_rejects_injection(self):
		self.assertFalse(is_valid_color('red; } * { background: red'))
	def test_rejects_nonsense(self):
		self.assertFalse(is_valid_color('#gg0000'))
		self.assertFalse(is_valid_color(12))

class TemplatesTest(TestCase):

	"""
	The guard that keeps colors out of the stylesheets. A hex literal that
	creeps back in would silently ignore the active theme; a mistyped $token
	would survive substitution and make tinycss reject the file, which takes
	the whole Core plugin down with it.
	"""

	def test_no_color_literals_left(self):
		for path in _TEMPLATES:
			self.assertEqual([], _COLOR_LITERAL.findall(_read(path)), path)
	def test_every_placeholder_is_a_known_token(self):
		for path in _TEMPLATES:
			for name in _PLACEHOLDER.findall(_read(path)):
				self.assertIn(name, DEFAULT_COLORS, '%s in %s' % (name, path))
	def test_every_token_is_used(self):
		used = set()
		for path in _TEMPLATES:
			used.update(_PLACEHOLDER.findall(_read(path)))
		used.update(_PALETTE_TOKENS)
		self.assertEqual(set(), set(DEFAULT_COLORS) - used)
	def test_substitution_leaves_no_placeholder(self):
		for path in _TEMPLATES:
			self.assertNotIn('$', substitute(_read(path), DEFAULT_COLORS), path)

class BundledThemesTest(TestCase):
	def test_default_theme_file_is_empty(self):
		# Monokai == DEFAULT_COLORS. An empty file is the only way to say
		# that without repeating every color.
		path = join(_THEMES_DIR, DEFAULT_THEME + '.json')
		self.assertTrue(exists(path), path)
		with open(path, 'r', encoding='utf-8') as f:
			self.assertEqual({}, json.load(f))
	def test_themes_are_valid(self):
		names = list_themes([_THEMES_DIR])
		self.assertIn(DEFAULT_THEME, names)
		self.assertEqual(11, len(names), names)
		for name in names:
			with open(join(_THEMES_DIR, name + '.json'), 'r') as f:
				data = json.load(f)
			for token, value in (data.get('colors') or {}).items():
				self.assertIn(token, DEFAULT_COLORS, '%s: %s' % (name, token))
				self.assertTrue(
					is_valid_color(value), '%s: %s=%r' % (name, token, value)
				)
			if 'opacity' in data:
				# Out of range would be silently ignored at runtime, which
				# in a *bundled* theme is a typo nobody would notice.
				self.assertEqual(
					data['opacity'], load_opacity(name, [_THEMES_DIR]),
					'%s: opacity=%r' % (name, data['opacity'])
				)
	def test_load_theme_falls_back_when_missing(self):
		self.assertEqual(DEFAULT_COLORS, load_theme('Nonexistent', [_THEMES_DIR]))
	def test_default_is_listed_without_any_dir(self):
		self.assertEqual([DEFAULT_THEME], list_themes([]))

class OpacityTest(TestCase):

	"""
	`opacity` is the one thing a theme may say that is not a color. It gets
	its own reader because resolve_colors drops everything that is not a
	valid color - a number could never survive inside "colors".
	"""

	def test_reads_the_key(self):
		self.assertEqual(0.8, self._load_opacity({'opacity': 0.8}))
	def test_reads_an_int(self):
		self.assertEqual(1.0, self._load_opacity({'opacity': 1}))
	def test_bundled_theme(self):
		self.assertEqual(0.92, load_opacity('Matrix', [_THEMES_DIR]))
	def test_theme_without_the_key(self):
		self.assertIsNone(load_opacity('Nord', [_THEMES_DIR]))
	def test_missing_theme(self):
		self.assertIsNone(load_opacity('Nonexistent', [_THEMES_DIR]))
	def test_rejects_a_string(self):
		self.assertIsNone(self._load_opacity({'opacity': '0.8'}))
	def test_rejects_a_bool(self):
		# True is an int in Python and would otherwise read as "opaque".
		self.assertIsNone(self._load_opacity({'opacity': True}))
	def test_rejects_too_transparent(self):
		self.assertIsNone(self._load_opacity({'opacity': MIN_OPACITY / 2}))
	def test_rejects_more_than_opaque(self):
		self.assertIsNone(self._load_opacity({'opacity': 1.5}))
	def test_non_dict_file_does_not_raise(self):
		# [] is valid JSON. Before this was guarded, .get('colors') on it
		# raised AttributeError out of load_theme - i.e. fman not starting.
		with TemporaryDirectory() as dir_:
			self._write(dir_, [])
			self.assertIsNone(load_opacity('T', [dir_]))
			self.assertEqual(DEFAULT_COLORS, load_theme('T', [dir_]))
	def _load_opacity(self, theme_json):
		with TemporaryDirectory() as dir_:
			self._write(dir_, theme_json)
			return load_opacity('T', [dir_])
	def _write(self, dir_, theme_json):
		with open(join(dir_, 'T.json'), 'w') as f:
			json.dump(theme_json, f)

# Every token the palette builders read. Kept next to the assertions below
# so the "every token is used" test above sees the palette-only ones too.
_PALETTE_TOKENS = frozenset((
	'window_bg', 'main_window_bg', 'base_bg', 'alt_row_bg', 'button_bg',
	'button_fg', 'palette_midlight', 'palette_mid', 'palette_dark',
	'palette_shadow', 'pane_cursor_bg', 'bright_fg'
))

class BuildPaletteTest(TestCase):

	"""
	Pins the palette to the values application_context.py hardcoded before
	themes existed, so the default theme is provably the old look.
	"""

	_EXPECTED = (
		(QPalette.Window, QColor(43, 43, 43)),
		(QPalette.WindowText, QColor('white')),
		(QPalette.Base, QColor(19, 19, 19)),
		(QPalette.AlternateBase, QColor(66, 64, 59)),
		(QPalette.ToolTipBase, QColor(19, 19, 19)),
		(QPalette.ToolTipText, QColor('white')),
		(QPalette.Light, QColor(0x49, 0x48, 0x3E)),
		(QPalette.Midlight, QColor(0x33, 0x33, 0x33)),
		(QPalette.Button, QColor(0x29, 0x29, 0x29)),
		(QPalette.Mid, QColor(0x25, 0x25, 0x25)),
		(QPalette.Dark, QColor(0x20, 0x20, 0x20)),
		(QPalette.Shadow, QColor(0x1d, 0x1d, 0x1d)),
		(QPalette.Text, QColor('white')),
		(QPalette.ButtonText, QColor(0xb6, 0xb3, 0xab)),
		(QPalette.Link, QColor('white')),
		(QPalette.LinkVisited, QColor('white'))
	)

	def test_matches_legacy_palette(self):
		palette = build_palette(DEFAULT_COLORS)
		for role, expected in self._EXPECTED:
			self.assertEqual(expected, palette.color(role), role)
	def test_inactive_highlight_avoids_blue(self):
		palette = build_palette(DEFAULT_COLORS)
		self.assertEqual(
			palette.color(QPalette.Midlight),
			palette.color(QPalette.Inactive, QPalette.Highlight)
		)
	def test_main_window_overrides_window_only(self):
		palette = build_main_window_palette(DEFAULT_COLORS)
		self.assertEqual(QColor(0x44, 0x44, 0x44), palette.color(QPalette.Window))
		self.assertEqual(QColor(19, 19, 19), palette.color(QPalette.Base))
	def test_progress_bar_keeps_highlight_when_inactive(self):
		palette = build_progress_bar_palette(DEFAULT_COLORS)
		self.assertEqual(
			palette.color(QPalette.Active, QPalette.Highlight),
			palette.color(QPalette.Inactive, QPalette.Highlight)
		)

def _relative_luminance(color):
	def channel(value):
		value /= 255
		return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4
	c = QColor(color)
	return 0.2126 * channel(c.red()) \
		+ 0.7152 * channel(c.green()) \
		+ 0.0722 * channel(c.blue())

def contrast_ratio(foreground, background):
	"""WCAG 2.1 contrast ratio, 1:1 (identical) to 21:1 (black on white)."""
	a, b = _relative_luminance(foreground), _relative_luminance(background)
	return (max(a, b) + 0.05) / (min(a, b) + 0.05)

class LegibilityTest(TestCase):

	"""
	Every bundled theme has to be readable, not merely valid. The command
	palette is the case that bit us: `popup_divider_*` used to fall back to
	`popup_bg`, so in every theme but Monokai the entry separators were the
	same color as the surface they sat on and the list read as one block.

	Monokai is exempt: it *is* the look fman shipped before themes existed
	(BuildPaletteTest and TemplatesTest pin those exact values), so changing
	its colors to satisfy a ratio would break the guarantee that the default
	theme is unchanged.
	"""

	_LEGACY = frozenset(['Monokai'])
	# WCAG AA for body text. The palette's smallest text (the description
	# line) is what this protects.
	_MIN_TEXT = 4.5
	# Separators and the selected row are large areas, not text: they only
	# have to be *distinguishable* from the surface behind them.
	_MIN_SEPARATOR = 1.15
	_MIN_SELECTION = 1.35

	_TEXT_PAIRS = (
		('entry title', 'popup_item_fg', 'popup_bg'),
		('matched characters', 'bright_fg', 'popup_bg'),
		('shortcut hint', 'bright_fg', 'popup_bg'),
		('entry description', 'muted_fg', 'popup_bg'),
		('title on selected row', 'popup_item_fg', 'popup_selected_bg'),
		('query field', 'popup_input_fg', 'popup_input_bg'),
		('file row', 'pane_fg', 'pane_bg'),
		('directory row', 'pane_fg_dir', 'pane_bg'),
		('column header', 'muted_fg', 'header_bg')
	)

	def test_palette_text_is_readable(self):
		for name, colors in self._themes():
			for what, fg, bg in self._TEXT_PAIRS:
				ratio = contrast_ratio(colors[fg], colors[bg])
				self.assertGreaterEqual(
					ratio, self._MIN_TEXT,
					'%s: %s is %.1f:1 (%s on %s)'
					% (name, what, ratio, colors[fg], colors[bg])
				)
	def test_palette_separators_are_visible(self):
		for name, colors in self._themes():
			for token in ('popup_divider_top', 'popup_divider_bottom'):
				ratio = contrast_ratio(colors[token], colors['popup_bg'])
				self.assertGreaterEqual(
					ratio, self._MIN_SEPARATOR,
					'%s: %s is invisible against popup_bg (%.2f:1)'
					% (name, token, ratio)
				)
	def test_selected_row_stands_out(self):
		for name, colors in self._themes():
			ratio = contrast_ratio(colors['popup_selected_bg'], colors['popup_bg'])
			self.assertGreaterEqual(
				ratio, self._MIN_SELECTION,
				'%s: selected row barely differs from the popup (%.2f:1)'
				% (name, ratio)
			)
	def test_no_separator_inherits_its_own_surface(self):
		# The root cause, asserted directly: a separator whose fallback is
		# the surface it is drawn on can never be seen, whatever the theme.
		for token in (
			'popup_divider_top', 'popup_divider_bottom',
			'popup_query_inner_border', 'popup_input_border'
		):
			self.assertNotEqual('popup_bg', FALLBACKS.get(token), token)
	def _themes(self):
		for name in list_themes([_THEMES_DIR]):
			if name not in self._LEGACY:
				yield name, load_theme(name, [_THEMES_DIR])
