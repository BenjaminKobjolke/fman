from core.commands.clipboard import CopyToClipboard, Cut, _report_clipboard_action
from core.commands.util import NO_SELECTION
from core.tests.commands import FakePane
from fman import DirectoryPane
from fman.url import as_human_readable, as_url
from unittest import TestCase
from unittest.mock import Mock, patch

class CopyItemTextTest(TestCase):
	def test_single_selected_items_copy_name_or_path(self):
		items = [
			('file://C:/folder/report.tar.gz', 'report.tar.gz'),
			('file://C:/folder/My Folder', 'My Folder'),
			('file://C:/folder/café.txt', 'café.txt'),
			('file:////server/share/Folder', 'Folder'),
			('zip://C:/archive.zip/folder/item.txt', 'item.txt')
		]
		for url, name in items:
			with self.subTest(url=url):
				self._assert_copy(url, name, 'CopyFileName')
				self._assert_copy(
					url, as_human_readable(url), 'CopyFilePath'
				)

	def test_cursor_fallback_and_invalid_counts(self):
		url = 'file://C:/folder/report.txt'
		for command_name in ('CopyFileName', 'CopyFilePath'):
			command_class = self._command_class(command_name)
			with self.subTest(command=command_name, case='cursor fallback'):
				pane = Mock(spec=DirectoryPane)
				pane.get_selected_files.return_value = []
				pane.get_file_under_cursor.return_value = url
				self._assert_copy_on_pane(
					command_class, pane,
					url.rsplit('/', 1)[-1] if command_name == 'CopyFileName'
					else as_human_readable(url)
				)
			with self.subTest(command=command_name, case='no selection'):
				pane = Mock(spec=DirectoryPane)
				pane.get_selected_files.return_value = []
				pane.get_file_under_cursor.return_value = None
				self._assert_not_copied(command_class, pane)
			with self.subTest(command=command_name, case='two selected'):
				pane = Mock(spec=DirectoryPane)
				pane.get_selected_files.return_value = [url, url + '2']
				self._assert_not_copied(command_class, pane)

	def test_execution_rechecks_selection(self):
		for command_name in ('CopyFileName', 'CopyFilePath'):
			with self.subTest(command=command_name):
				pane = Mock(spec=DirectoryPane)
				pane.get_selected_files.side_effect = [
					['file://C:/folder/report.txt'],
					['file://C:/folder/report.txt', 'file://C:/folder/other.txt']
				]
				pane.get_file_under_cursor.return_value = None
				command_class = self._command_class(command_name)
				command = command_class(pane)
				self.assertTrue(command.is_visible())
				with patch(
					'core.commands.clipboard.clipboard.clear'
				) as clear, patch(
					'core.commands.clipboard.clipboard.set_text'
				) as set_text, patch(
					'core.commands.clipboard.show_status_message'
				) as status:
					command()
				clear.assert_not_called()
				set_text.assert_not_called()
				status.assert_not_called()

	def _assert_copy(self, url, name, command_name):
		pane = Mock(spec=DirectoryPane)
		pane.get_selected_files.return_value = [url]
		text = name if command_name == 'CopyFileName' else as_human_readable(url)
		self._assert_copy_on_pane(self._command_class(command_name), pane, text)

	def _assert_copy_on_pane(self, command_class, pane, text):
		command = command_class(pane)
		self.assertTrue(command.is_visible())
		with patch('core.commands.clipboard.clipboard.clear') as clear, \
				patch('core.commands.clipboard.clipboard.set_text') as set_text, \
				patch('core.commands.clipboard.show_status_message') as status:
			command()
		clear.assert_called_once_with()
		set_text.assert_called_once_with(text)
		status.assert_called_once_with(
			'Copied %s to the clipboard' % text, timeout_secs=3
		)
		pane.get_path.assert_not_called()

	def _assert_not_copied(self, command_class, pane):
		command = command_class(pane)
		self.assertFalse(command.is_visible())
		with patch('core.commands.clipboard.clipboard.clear') as clear, \
				patch('core.commands.clipboard.clipboard.set_text') as set_text, \
				patch('core.commands.clipboard.show_status_message') as status:
			command()
		clear.assert_not_called()
		set_text.assert_not_called()
		status.assert_not_called()

	def _command_class(self, name):
		from core import commands
		return getattr(commands, name)

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
