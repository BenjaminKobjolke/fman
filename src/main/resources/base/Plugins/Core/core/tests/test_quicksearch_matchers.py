from core.quicksearch_matchers import \
	contains_chars_after_separator, contains_chars_any_order
from unittest import TestCase

class ContainsCharsAfterSeparatorTest(TestCase):
	def test_simple(self):
		self.assertEqual(
			[0, 5], self.find_chars_after_space('copy paths', 'cp')
		)
	def test_chars_in_first_and_second_part(self):
		self.assertEqual(
			[0, 1, 2], self.find_chars_after_space('copy paths', 'cop')
		)
	def test_no_match(self):
		self.assertIsNone(self.find_chars_after_space('copy paths', 'cd'))
	def test_full_word_match(self):
		self.assertEqual(
			[0, 1, 2, 3, 5],
			self.find_chars_after_space('copy paths', 'copyp')
		)
	def test_prefix_match(self):
		self.assertEqual(
			[0, 1],
			self.find_chars_after_space('column count', 'co')
		)
	def setUp(self):
		super().setUp()
		self.find_chars_after_space = contains_chars_after_separator(' ')

class ContainsCharsAnyOrderTest(TestCase):
	def test_reversed_order_matches(self):
		result = contains_chars_any_order('show all panes', 'panes show')
		self.assertIsNotNone(result)
		# Highlights both the 'show' and 'panes' words:
		self.assertEqual([0, 1, 2, 3, 9, 10, 11, 12, 13], result)
	def test_in_order_matches(self):
		self.assertIsNotNone(
			contains_chars_any_order('show all panes', 'show panes')
		)
	def test_missing_word_is_no_match(self):
		self.assertIsNone(
			contains_chars_any_order('show all panes', 'panes missing')
		)
	def test_empty_query_is_no_match(self):
		self.assertIsNone(contains_chars_any_order('show all panes', ''))