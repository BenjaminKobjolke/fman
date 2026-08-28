from core.command_titles import apply_custom_title, get_custom_title
from unittest import TestCase
from unittest.mock import patch

class GetCustomTitleTest(TestCase):

	def test_no_override(self):
		self.assertEqual('', self._get({}, 'quit'))
	def test_renamed_command(self):
		self.assertEqual('Exit', self._get({'quit': 'Exit'}, 'quit'))
	def test_title_is_stripped(self):
		self.assertEqual('Exit', self._get({'quit': '  Exit  '}, 'quit'))
	def test_empty_command_name(self):
		self.assertEqual('', self._get({'quit': 'Exit'}, ''))
	def test_blank_title_is_ignored(self):
		self.assertEqual('', self._get({'quit': '   '}, 'quit'))
	def test_non_string_value_is_ignored(self):
		# The file is user-editable, so a wrong shape must not raise inside
		# the palette's per-keystroke callback.
		self.assertEqual('', self._get({'quit': ['Exit']}, 'quit'))

	def _get(self, settings, command_name):
		with _titles(settings):
			return get_custom_title(command_name)

class ApplyCustomTitleTest(TestCase):

	def test_without_an_override_nothing_changes(self):
		self.assertEqual(
			(['Quit', 'Exit fman'], ('bye',)),
			self._apply({}, 'quit', ['Quit', 'Exit fman'], ('bye',))
		)
	def test_the_custom_title_replaces_the_original_ones(self):
		titles, _keywords = self._apply(
			{'quit': 'Exit'}, 'quit', ['Quit', 'Exit fman'], ()
		)
		self.assertEqual(['Exit'], titles)
	def test_the_original_titles_become_keywords(self):
		_titles_, keywords = self._apply(
			{'quit': 'Exit'}, 'quit', ['Quit', 'Exit fman'], ('bye',)
		)
		self.assertEqual(('bye', 'quit', 'exit fman'), keywords)

	def _apply(self, settings, command_name, titles, keywords):
		with _titles(settings):
			return apply_custom_title(command_name, titles, keywords)

def _titles(settings):
	return patch(
		'core.command_titles.get_setting',
		side_effect=lambda _json, key, default: settings.get(key, default)
	)
