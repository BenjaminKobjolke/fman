from core.commands.theme import CURRENT_HINT, ICON_COLOR_NAMES, \
	ICON_COLOR_PRESETS, ICON_SIZE_PRESETS, OPACITY_PRESETS, \
	THEME_DEFAULT_LABEL, ResetFont, SelectFont, SelectIconSet, \
	SelectTheme, SetIconColor, SetIconSize, SetWindowOpacity, \
	get_font_items, get_icon_color_items, get_icon_set_items, \
	get_icon_size_items, get_opacity_items, get_theme_items
from unittest import TestCase

_NAMES = ['Dracula', 'Monokai', 'Nord']
_ICON_SETS = ['Material', 'System']
_FONTS = ['Fira Code', 'JetBrains Mono', 'Share Tech Mono']

class GetThemeItemsTest(TestCase):
	def test_empty_query_keeps_given_order(self):
		# SelectTheme preselects by index into the unfiltered list, so this
		# order has to match the one it passes in.
		items = get_theme_items(_NAMES, 'Monokai', '')
		self.assertEqual(_NAMES, [item.value for item in items])
	def test_filters_by_query(self):
		items = get_theme_items(_NAMES, 'Monokai', 'nrd')
		self.assertEqual(['Nord'], [item.value for item in items])
	def test_marks_the_current_theme(self):
		hints = {
			item.value: item.hint
			for item in get_theme_items(_NAMES, 'Monokai', '')
		}
		self.assertEqual(CURRENT_HINT, hints['Monokai'])
		self.assertEqual('', hints['Nord'])
	def test_no_match(self):
		self.assertEqual([], get_theme_items(_NAMES, 'Monokai', 'zzz'))

class SelectThemeTest(TestCase):
	def test_has_expected_aliases(self):
		self.assertIn('Select theme', SelectTheme.aliases)

class GetOpacityItemsTest(TestCase):
	def test_empty_query_keeps_given_order(self):
		# SetWindowOpacity preselects by index into the unfiltered list.
		items = get_opacity_items(1.0, '')
		self.assertEqual(
			[None] + list(OPACITY_PRESETS), [item.value for item in items]
		)
	def test_theme_default_comes_first(self):
		items = get_opacity_items(1.0, '')
		self.assertEqual(THEME_DEFAULT_LABEL, items[0].title)
		self.assertIsNone(items[0].value)
	def test_labels_are_percentages(self):
		titles = {item.value: item.title for item in get_opacity_items(1.0, '')}
		self.assertEqual('100%', titles[1.0])
		self.assertEqual('75%', titles[0.75])
	def test_filters_by_query(self):
		items = get_opacity_items(1.0, '75')
		self.assertEqual([0.75], [item.value for item in items])
	def test_marks_the_current_value(self):
		hints = {item.value: item.hint for item in get_opacity_items(0.8, '')}
		self.assertEqual(CURRENT_HINT, hints[0.8])
		self.assertEqual('', hints[1.0])
	def test_marks_nothing_for_a_value_without_a_preset(self):
		# A theme may ask for any opacity, e.g. Matrix's 0.92.
		hints = [item.hint for item in get_opacity_items(0.92, '')]
		self.assertEqual([''] * len(hints), hints)
	def test_no_match(self):
		self.assertEqual([], get_opacity_items(1.0, 'zzz'))

class SetWindowOpacityTest(TestCase):
	def test_has_expected_aliases(self):
		self.assertIn('Set window opacity', SetWindowOpacity.aliases)

class GetIconSetItemsTest(TestCase):
	def test_empty_query_keeps_given_order(self):
		# SelectIconSet preselects by index into the unfiltered list.
		items = get_icon_set_items(_ICON_SETS, 'System', '')
		self.assertEqual(_ICON_SETS, [item.value for item in items])
	def test_has_no_theme_default_entry(self):
		# Unlike opacity and icon size, "System" already is the way back:
		# it is a set name of its own, so a None entry would say it twice.
		values = [item.value for item in get_icon_set_items(_ICON_SETS, 'System', '')]
		self.assertNotIn(None, values)
	def test_filters_by_query(self):
		items = get_icon_set_items(_ICON_SETS, 'System', 'mtl')
		self.assertEqual(['Material'], [item.value for item in items])
	def test_marks_the_current_set(self):
		hints = {
			item.value: item.hint
			for item in get_icon_set_items(_ICON_SETS, 'Material', '')
		}
		self.assertEqual(CURRENT_HINT, hints['Material'])
		self.assertEqual('', hints['System'])
	def test_no_match(self):
		self.assertEqual([], get_icon_set_items(_ICON_SETS, 'System', 'zzz'))

class SelectIconSetTest(TestCase):
	def test_has_expected_aliases(self):
		self.assertIn('Select icon set', SelectIconSet.aliases)

class GetFontItemsTest(TestCase):
	def test_empty_query_keeps_given_order(self):
		# SelectFont preselects by index into the unfiltered list.
		items = get_font_items(_FONTS, 'Fira Code', '')
		self.assertEqual(
			[None] + _FONTS, [item.value for item in items]
		)
	def test_theme_default_comes_first(self):
		# Unlike an icon set, no family name means 'stop overriding', so
		# the way back has to be an entry of its own.
		items = get_font_items(_FONTS, 'Fira Code', '')
		self.assertEqual(THEME_DEFAULT_LABEL, items[0].title)
		self.assertIsNone(items[0].value)
	def test_filters_by_query(self):
		items = get_font_items(_FONTS, 'Fira Code', 'jbm')
		self.assertEqual(['JetBrains Mono'], [item.value for item in items])
	def test_marks_the_current_font(self):
		hints = {
			item.value: item.hint
			for item in get_font_items(_FONTS, 'JetBrains Mono', '')
		}
		self.assertEqual(CURRENT_HINT, hints['JetBrains Mono'])
		self.assertEqual('', hints['Fira Code'])
	def test_marks_nothing_for_a_font_that_is_not_listed(self):
		# get_font() answers the platform default, which need not be one of
		# the families Qt reports under that exact name.
		hints = [item.hint for item in get_font_items(_FONTS, 'Nope', '')]
		self.assertEqual([''] * len(hints), hints)
	def test_no_match(self):
		self.assertEqual([], get_font_items(_FONTS, 'Fira Code', 'zzz'))

class SelectFontTest(TestCase):
	def test_has_expected_aliases(self):
		self.assertIn('Select font', SelectFont.aliases)

class ResetFontTest(TestCase):
	def test_has_expected_aliases(self):
		self.assertIn('Reset font', ResetFont.aliases)

class GetIconSizeItemsTest(TestCase):
	def test_empty_query_keeps_given_order(self):
		items = get_icon_size_items(None, '')
		self.assertEqual(
			[None] + list(ICON_SIZE_PRESETS), [item.value for item in items]
		)
	def test_theme_default_comes_first(self):
		items = get_icon_size_items(None, '')
		self.assertEqual(THEME_DEFAULT_LABEL, items[0].title)
		self.assertIsNone(items[0].value)
	def test_labels_are_pixels(self):
		titles = {item.value: item.title for item in get_icon_size_items(None, '')}
		self.assertEqual('16 px', titles[16])
		self.assertEqual('32 px', titles[32])
	def test_marks_the_current_value(self):
		hints = {item.value: item.hint for item in get_icon_size_items(24, '')}
		self.assertEqual(CURRENT_HINT, hints[24])
		self.assertEqual('', hints[16])
	def test_marks_theme_default_when_no_size_is_set(self):
		# get_icon_size() returns None when neither the user nor the theme
		# asks for a size, and that is exactly the "Theme default" entry.
		hints = {item.value: item.hint for item in get_icon_size_items(None, '')}
		self.assertEqual(CURRENT_HINT, hints[None])
	def test_marks_nothing_for_a_size_without_a_preset(self):
		hints = [item.hint for item in get_icon_size_items(21, '')]
		self.assertEqual([''] * len(hints), hints)
	def test_no_match(self):
		self.assertEqual([], get_icon_size_items(None, 'zzz'))

class GetIconColorItemsTest(TestCase):
	def test_empty_query_keeps_given_order(self):
		items = get_icon_color_items(None, '')
		self.assertEqual(
			[None] + list(ICON_COLOR_PRESETS),
			[item.value for item in items]
		)
	def test_theme_default_comes_first(self):
		items = get_icon_color_items(None, '')
		self.assertEqual(THEME_DEFAULT_LABEL, items[0].title)
		self.assertIsNone(items[0].value)
	def test_labels_are_names_not_hex(self):
		# The value a theme file would carry is the hex, but a list of hex
		# codes is not something anyone can pick from.
		titles = {
			item.value: item.title
			for item in get_icon_color_items(None, '')
		}
		self.assertEqual('Green', titles['#00ff41'])
	def test_every_preset_has_a_name(self):
		self.assertEqual(
			len(ICON_COLOR_PRESETS), len(dict(ICON_COLOR_NAMES))
		)
	def test_marks_the_current_value(self):
		hints = {
			item.value: item.hint
			for item in get_icon_color_items('#00ff41', '')
		}
		self.assertEqual(CURRENT_HINT, hints['#00ff41'])
		self.assertEqual('', hints['#ff5252'])
	def test_marks_theme_default_when_no_color_is_set(self):
		hints = {
			item.value: item.hint
			for item in get_icon_color_items(None, '')
		}
		self.assertEqual(CURRENT_HINT, hints[None])
	def test_finds_a_color_by_name(self):
		items = get_icon_color_items(None, 'green')
		self.assertEqual(['#00ff41'], [item.value for item in items])
	def test_no_match(self):
		self.assertEqual([], get_icon_color_items(None, 'zzz'))

class SetIconColorTest(TestCase):
	def test_has_expected_aliases(self):
		self.assertIn('Set icon color', SetIconColor.aliases)

class SetIconSizeTest(TestCase):
	def test_has_expected_aliases(self):
		self.assertIn('Set icon size', SetIconSize.aliases)
