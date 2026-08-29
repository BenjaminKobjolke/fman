from core.commands.window import _format_window_title
from unittest import TestCase

class FormatWindowTitleTest(TestCase):
	def test_no_paths(self):
		self.assertEqual('fman - file manager', _format_window_title([]))
	def test_blank_paths_skipped(self):
		self.assertEqual('fman - file manager', _format_window_title(['', '']))
	def test_one_path(self):
		self.assertEqual(
			'fman - file manager - C:\\test',
			_format_window_title(['C:\\test'])
		)
	def test_two_paths(self):
		self.assertEqual(
			'fman - file manager - C:\\test | D:\\other',
			_format_window_title(['C:\\test', 'D:\\other'])
		)
