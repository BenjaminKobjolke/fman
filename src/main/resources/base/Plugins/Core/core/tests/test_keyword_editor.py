from core.keyword_editor import edit_command_keywords
from unittest import TestCase
from unittest.mock import patch

class _Screens:

	"""
	Drives the menu chain without Qt: show_quicksearch is replaced by a queue
	of answers, one per screen that opens - a string picks that option, None
	means Escape. Also records the option lists each screen offered.
	"""

	def __init__(self, answers, keywords, prompt=None):
		self._answers = list(answers)
		self.keywords = dict(keywords)
		self._prompt = prompt
		self.shown = []
	def show_quicksearch(self, get_items, *_args, **_kwargs):
		options = [item.value for item in get_items('')]
		self.shown.append(options)
		answer = self._answers.pop(0) if self._answers else None
		if answer is None:
			return None
		return '', answer
	def show_prompt(self, _text, *_args, **_kwargs):
		if self._prompt is None:
			return '', False
		return self._prompt, True
	def get_setting(self, _json_name, key, default=None):
		return self.keywords.get(key, default)
	def save_setting(self, _json_name, key, value):
		self.keywords[key] = value

def _run(answers, keywords, prompt=None, command='video_mute', title='Mute'):
	screens = _Screens(answers, keywords, prompt)
	with patch(
		'core.quicksearch_screen.show_quicksearch',
		side_effect=screens.show_quicksearch
	), patch(
		'core.keyword_editor.show_prompt', side_effect=screens.show_prompt
	), patch(
		'core.keyword_editor.get_setting', side_effect=screens.get_setting
	), patch(
		'core.keyword_editor.save_setting', side_effect=screens.save_setting
	):
		edit_command_keywords(command, title)
	return screens

class EditCommandKeywordsTest(TestCase):

	def test_entry_menu_offers_changing_the_keywords(self):
		screens = _run([None], {'video_mute': ['sound']})
		self.assertEqual([['Change keywords for "Mute"']], screens.shown)
	def test_keyword_list_shows_add_then_the_keywords(self):
		screens = _run(
			['Change keywords for "Mute"', None], {'video_mute': ['sound', 'volume']}
		)
		self.assertEqual(
			['Add keyword...', 'sound', 'volume'], screens.shown[1]
		)
	def test_a_command_without_keywords_still_offers_add(self):
		screens = _run(['Change keywords for "Mute"', None], {})
		self.assertEqual(['Add keyword...'], screens.shown[1])
	def test_escape_on_the_entry_menu_changes_nothing(self):
		screens = _run([None], {'video_mute': ['sound']})
		self.assertEqual({'video_mute': ['sound']}, screens.keywords)
	def test_no_command_name_saves_nothing(self):
		screens = _run([None], {}, command='')
		self.assertEqual([], screens.shown)

class AddKeywordTest(TestCase):

	def test_adds_the_typed_keyword(self):
		screens = _run(
			['Change keywords for "Mute"', 'Add keyword...', None],
			{'video_mute': ['sound']}, prompt='volume'
		)
		self.assertEqual(['sound', 'volume'], screens.keywords['video_mute'])
	def test_keyword_is_lowercased_and_stripped(self):
		screens = _run(
			['Change keywords for "Mute"', 'Add keyword...', None], {},
			prompt='  Volume  '
		)
		self.assertEqual(['volume'], screens.keywords['video_mute'])
	def test_duplicate_is_not_added_twice(self):
		screens = _run(
			['Change keywords for "Mute"', 'Add keyword...', None],
			{'video_mute': ['sound']}, prompt='Sound'
		)
		self.assertEqual({'video_mute': ['sound']}, screens.keywords)
	def test_empty_keyword_is_ignored(self):
		screens = _run(
			['Change keywords for "Mute"', 'Add keyword...', None],
			{'video_mute': ['sound']}, prompt='   '
		)
		self.assertEqual({'video_mute': ['sound']}, screens.keywords)
	def test_cancelled_prompt_saves_nothing(self):
		screens = _run(
			['Change keywords for "Mute"', 'Add keyword...', None],
			{'video_mute': ['sound']}
		)
		self.assertEqual({'video_mute': ['sound']}, screens.keywords)
	def test_the_list_reopens_after_adding(self):
		screens = _run(
			['Change keywords for "Mute"', 'Add keyword...', None], {},
			prompt='volume'
		)
		self.assertEqual(['Add keyword...', 'volume'], screens.shown[-1])

class DeleteKeywordTest(TestCase):

	def test_keyword_menu_offers_delete_and_go_back(self):
		screens = _run(
			['Change keywords for "Mute"', 'sound', None],
			{'video_mute': ['sound']}
		)
		self.assertEqual(['Delete', 'Go back'], screens.shown[2])
	def test_delete_removes_only_that_keyword(self):
		screens = _run(
			['Change keywords for "Mute"', 'sound', 'Delete', None],
			{'video_mute': ['sound', 'volume']}
		)
		self.assertEqual(['volume'], screens.keywords['video_mute'])
	def test_deleting_the_last_keyword_writes_an_empty_list(self):
		# Not None: that would pop the key, and popping one the shipped file
		# still defines makes the differential write raise ValueError.
		screens = _run(
			['Change keywords for "Mute"', 'sound', 'Delete', None],
			{'video_mute': ['sound']}
		)
		self.assertEqual([], screens.keywords['video_mute'])
	def test_go_back_keeps_the_keyword(self):
		screens = _run(
			['Change keywords for "Mute"', 'sound', 'Go back', None],
			{'video_mute': ['sound']}
		)
		self.assertEqual({'video_mute': ['sound']}, screens.keywords)
		self.assertEqual(['Add keyword...', 'sound'], screens.shown[-1])
	def test_escape_on_the_keyword_menu_returns_to_the_list(self):
		screens = _run(
			['Change keywords for "Mute"', 'sound', None, None],
			{'video_mute': ['sound']}
		)
		self.assertEqual(['Add keyword...', 'sound'], screens.shown[-1])

class MalformedFileTest(TestCase):

	"""
	Command Keywords.json is user-editable, so the editor must survive shapes
	get_keywords already tolerates - see tests/test_command_keywords.py.
	"""

	def test_non_string_entries_are_dropped(self):
		screens = _run(
			['Change keywords for "Mute"', None], {'video_mute': ['sound', 7]}
		)
		self.assertEqual(['Add keyword...', 'sound'], screens.shown[1])
