from core.command_keywords import COMMAND_KEYWORDS_FILE, get_keywords
from os.path import dirname, join
from unittest import TestCase
from unittest.mock import patch

import json

class GetKeywordsTest(TestCase):

	def test_unknown_command_has_no_keywords(self):
		self.assertEqual((), self._get_keywords({}, 'quit'))
	def test_known_command(self):
		self.assertEqual(
			('bye', 'exit'),
			self._get_keywords({'quit': ['bye', 'exit']}, 'quit')
		)
	def test_terms_are_lowercased(self):
		self.assertEqual(
			('bye',), self._get_keywords({'quit': ['Bye']}, 'quit')
		)
	def test_empty_command_name(self):
		self.assertEqual((), self._get_keywords({'quit': ['bye']}, ''))
	def test_non_list_value_is_ignored(self):
		# The file is user-editable, so a wrong shape must not raise inside
		# the palette's per-keystroke callback.
		self.assertEqual((), self._get_keywords({'quit': 'bye'}, 'quit'))
	def test_non_string_items_are_dropped(self):
		self.assertEqual(
			('bye',), self._get_keywords({'quit': ['bye', 7, None]}, 'quit')
		)

	def _get_keywords(self, settings, command_name):
		with patch(
			'core.command_keywords.get_setting',
			side_effect=lambda _json, key, default: settings.get(key, default)
		):
			return get_keywords(command_name)

class ShippedKeywordsFileTest(TestCase):

	"""
	Guards the data file itself: a typo there would otherwise just silently
	stop a keyword from working, with nothing failing anywhere.
	"""

	def test_every_value_is_a_list_of_lowercase_strings(self):
		for command_name, keywords in self._load().items():
			with self.subTest(command=command_name):
				self.assertIsInstance(keywords, list)
				self.assertTrue(keywords, 'Empty keyword list')
				for keyword in keywords:
					self.assertIsInstance(keyword, str)
					self.assertEqual(keyword.lower(), keyword)
	def test_no_duplicate_keywords_per_command(self):
		for command_name, keywords in self._load().items():
			with self.subTest(command=command_name):
				self.assertEqual(len(set(keywords)), len(keywords))

	def _load(self):
		# core/tests/ -> core/ -> Plugins/Core/, where the JSON ships.
		path = join(
			dirname(dirname(dirname(__file__))), COMMAND_KEYWORDS_FILE
		)
		with open(path, 'r', encoding='utf-8') as f:
			return json.load(f)
