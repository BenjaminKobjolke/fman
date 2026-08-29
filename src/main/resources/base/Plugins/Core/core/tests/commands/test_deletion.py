from core.commands.deletion import _describe
from fman.url import as_url
from unittest import TestCase

class DescribeTest(TestCase):

	"""
	`_describe` names a single file but only counts several, and the caller
	picks the wording of the count ('these %d files' in a confirmation, the
	default '%d files' in a task title).
	"""

	def test_one_file_is_named_not_counted(self):
		self.assertEqual('a.txt', _describe([as_url('/dir/a.txt')]))
	def test_several_files_are_counted_with_the_default_template(self):
		self.assertEqual('2 files', _describe(self._urls('a', 'b')))
	def test_the_template_is_applied(self):
		self.assertEqual(
			'these 3 items',
			_describe(self._urls('a', 'b', 'c'), 'these %d items')
		)
	def test_the_template_is_ignored_for_a_single_file(self):
		self.assertEqual(
			'a', _describe(self._urls('a'), 'these %d items')
		)
	def _urls(self, *names):
		return [as_url('/dir/' + name) for name in names]
