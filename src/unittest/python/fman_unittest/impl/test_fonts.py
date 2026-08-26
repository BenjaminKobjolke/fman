"""
The vendoring guard for the bundled font families, the font counterpart
of test_icon_set.BundledIconSetTest.

A family that ships without a Regular silently falls back to Qt's own
font at runtime; one that ships without its licence is a distribution
problem rather than a visible bug; and a woff2 that slipped in is a font
that never appears, because addApplicationFont answers -1 and the plugin
loader only reports that. None of the three is something a theme file or
a screenshot would reveal.
"""
from fman.impl.theme_controller import ThemeController, _FONT
from fman.impl.themes import DEFAULT_FONT, FONT_SETTING, THEME_SETTING
from glob import glob
from json import dump
from os.path import basename, dirname, exists, isdir, join
from tempfile import TemporaryDirectory
from unittest import TestCase

_PROJECT_DIR = dirname(dirname(dirname(dirname(dirname(dirname(
	__file__
))))))
FONTS_DIR = join(
	_PROJECT_DIR, 'src', 'main', 'resources', 'base', 'Plugins', 'Core',
	'Fonts'
)

def bundled_font_families():
	"""
	The families fman ships, which are the names of the directories under
	Plugins/Core/Fonts. tools/fetch_google_fonts.py names each directory
	after the family it read out of the font's own name table, so this is
	the string QFontDatabase reports - and therefore the string a theme
	has to write. BundledFontsTest below is what keeps that true, and
	test_themes.BundledThemesTest is what holds the themes to it.
	"""
	return sorted(
		basename(path) for path in glob(join(FONTS_DIR, '*'))
		if isdir(path)
	)

class BundledFontsTest(TestCase):

	"""
	The vendoring guard, the font counterpart of
	test_icon_set.BundledIconSetTest. A family that ships without a
	Regular would silently fall back to Qt's own font at runtime, and one
	that ships without its licence would be a distribution problem rather
	than a visible bug - neither is something a theme file can reveal.
	"""

	def test_families_are_bundled(self):
		self.assertTrue(bundled_font_families(), FONTS_DIR)
	def test_every_family_ships_a_face(self):
		# Not specifically a Regular: Roboto and Open Sans predate the
		# feature and ship as a single Bold / Semibold face, which is the
		# weight fman's UI has always been drawn in. A family with no file
		# at all is the real bug - it would be a name nothing can draw.
		for family in bundled_font_families():
			with self.subTest(family):
				self.assertTrue(
					glob(join(FONTS_DIR, family, '*.ttf')), family
				)
	def test_every_family_ships_its_license(self):
		for family in bundled_font_families():
			with self.subTest(family):
				path = join(FONTS_DIR, family, 'LICENSE')
				self.assertTrue(exists(path), path)
				self.assertTrue(_read(path).strip(), path)
	def test_every_font_file_is_a_truetype(self):
		# addApplicationFont answers -1 for anything else, and the plugin
		# loader only reports that - it does not raise - so a woff2 that
		# slipped in would be a font that silently never appears.
		for family in bundled_font_families():
			for path in glob(join(FONTS_DIR, family, '*.ttf')):
				with self.subTest(path):
					with open(path, 'rb') as f:
						self.assertIn(
							f.read(4), (b'\x00\x01\x00\x00', b'true', b'ttcf'), path
						)


def _read(path):
	with open(path, 'r', encoding='utf-8') as f:
		return f.read()

class _StubSettings(dict):
	"""What ThemeController needs of impl/util/settings.Settings."""

	def pop(self, key, default=None):
		return super().pop(key, default)

	def flush(self):
		pass

class _StubContext:
	def __init__(self, theme_dirs, settings):
		self.theme_dirs = theme_dirs
		self.local_settings = settings

class FontPrecedenceTest(TestCase):

	"""
	The rule that makes "Select font" worth having: the user's own choice
	outranks the theme's and survives a theme switch. ThemeController._get
	is shared by all five non-color properties, but only the font's wiring
	is new - the others are covered through their own commands.
	"""

	def test_theme_font_applies_when_the_user_has_none(self):
		self.assertEqual('Fira Code', self._controller('Fira Code').get_font())
	def test_platform_default_when_neither_asks(self):
		self.assertEqual(DEFAULT_FONT, self._controller(None).get_font())
	def test_user_font_beats_the_theme(self):
		controller = self._controller('Fira Code', saved='JetBrains Mono')
		self.assertEqual('JetBrains Mono', controller.get_font())
	def test_unusable_saved_font_falls_through_to_the_theme(self):
		# _get normalizes the saved value too, so a hand-edited Settings.json
		# cannot inject into the stylesheet the theme files are guarded from.
		controller = self._controller('Fira Code', saved='x; } * { color: red')
		self.assertEqual('Fira Code', controller.get_font())
	def test_none_clears_the_override(self):
		controller = self._controller('Fira Code', saved='JetBrains Mono')
		controller._save(_FONT, None)
		self.assertEqual('Fira Code', controller.get_font())
	def _controller(self, theme_font, saved=None):
		dir_ = TemporaryDirectory()
		self.addCleanup(dir_.cleanup)
		theme = {} if theme_font is None else {'font': theme_font}
		with open(join(dir_.name, 'T.json'), 'w') as f:
			dump(theme, f)
		settings = _StubSettings({THEME_SETTING: 'T'})
		if saved is not None:
			settings[FONT_SETTING] = saved
		return ThemeController(_StubContext([dir_.name], settings))
