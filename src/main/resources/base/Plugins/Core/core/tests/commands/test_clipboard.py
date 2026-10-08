from core.commands.clipboard import CopyToClipboard, Cut, _report_clipboard_action
from core.commands.util import NO_SELECTION
from core.tests.commands import FakePane
from fman.url import as_human_readable, as_url
from unittest import TestCase
from unittest.mock import patch

class NoSelectionTest(TestCase):
	def test_copy_alerts_when_nothing_is_chosen(self):
		with patch.object(CopyToClipboard, 'get_chosen_files', return_value=[]), \
			 patch('core.commands.clipboard.show_alert') as show_alert:
			CopyToClipboard(FakePane())()
		show_alert.assert_called_once_with(NO_SELECTION)

	def test_cut_alerts_when_nothing_is_chosen(self):
		with patch.object(Cut, 'get_chosen_files', return_value=[]), \
			 patch('core.commands.clipboard.PLATFORM', 'Windows'), \
			 patch('core.commands.clipboard.show_alert') as show_alert:
			Cut(FakePane())()
		show_alert.assert_called_once_with(NO_SELECTION)

class ReportClipboardActionTest(TestCase):

	"""
	The status message names the first file and counts the rest, so its
	plural has to follow the *remainder*, not the total: two files leave one
	other, which is singular.
	"""

	def test_one_file(self):
		self.assertEqual('Copying %s' % self._path('a'), self._report(['a']))
	def test_two_files_says_one_other_singular(self):
		self.assertEqual(
			'Copying %s and 1 other file' % self._path('a'),
			self._report(['a', 'b'])
		)
	def test_three_files_says_two_others_plural(self):
		self.assertEqual(
			'Copying %s and 2 other files' % self._path('a'),
			self._report(['a', 'b', 'c'])
		)
	def test_suffix_and_type_are_applied(self):
		self.assertEqual(
			'Copied %s and 1 other path to the clipboard' % self._path('a'),
			self._report(['a', 'b'], 'Copied', ' to the clipboard', 'path')
		)
	def _report(self, names, verb='Copying', suffix='', ftype='file'):
		urls = [self._url(name) for name in names]
		with patch(
			'core.commands.clipboard.show_status_message'
		) as show_status_message:
			_report_clipboard_action(verb, urls, suffix, ftype)
		(message,), _kwargs = show_status_message.call_args
		return message
	def _url(self, name):
		return as_url('/dir/' + name)
	def _path(self, name):
		return as_human_readable(self._url(name))
