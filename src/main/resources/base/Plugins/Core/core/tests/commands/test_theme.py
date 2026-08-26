from core.commands.theme import CURRENT_HINT, OPACITY_PRESETS, \
	THEME_DEFAULT_LABEL, SelectTheme, SetWindowOpacity, get_opacity_items, \
	get_theme_items
from unittest import TestCase

_NAMES = ['Dracula', 'Monokai', 'Nord']

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
