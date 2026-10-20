from core.commands import deletion
from core.commands.deletion import _describe, DeletePermanently
from fman import DirectoryPane, PLATFORM, Task, YES
from fman.url import as_url
from unittest import TestCase
from unittest.mock import Mock, patch

class TrashTest(TestCase):
	def test_trash_with_unsupported_url_deletes_nothing(self):
		urls = ['file://C:/a.zip', 'zip://C:/a.zip/report.txt']
		local_task = Mock(spec=Task)
		local_task.get_size.return_value = 1
		def prepare_trash(url):
			if url.startswith('zip://'):
				raise NotImplementedError()
			return [local_task]
		with patch('core.commands.deletion.prepare_trash',
				 side_effect=prepare_trash), \
			 patch('core.commands.deletion.prepare_delete',
				 side_effect=AssertionError('Permanent delete fallback')), \
			 patch('core.commands.deletion.submit_task') as submit_task, \
			 patch('core.commands.deletion.elevation.delete', return_value=False):
			deletion.trash(urls)
		delete_task = submit_task.call_args.args[0]
		with patch.object(delete_task, 'run') as run, \
			 patch.object(delete_task, 'show_alert') as show_alert:
			delete_task()
		run.assert_not_called()
		trash_name = 'Recycle Bin' if PLATFORM == 'Windows' else 'Trash'
		show_alert.assert_called_once_with(
			'The %s is not available in zip://. Nothing was deleted. '
			'Use Delete permanently instead.' % trash_name
		)
	def test_delete_permanently_reports_unsupported_filesystem(self):
		with patch('core.commands.deletion.show_alert', return_value=YES), \
			 patch('core.commands.deletion.elevation.delete', return_value=False), \
				 patch('core.commands.deletion.submit_task') as submit_task, \
				 patch('core.commands.deletion.prepare_delete',
					 side_effect=NotImplementedError):
			DeletePermanently(Mock(spec=DirectoryPane))(
				urls=['zip://archive.zip/file.txt']
			)
		delete_task = submit_task.call_args.args[0]
		with patch.object(delete_task, 'show_alert') as show_alert:
			delete_task()
		show_alert.assert_called_once_with(
			'Deleting files in zip:// is not supported.'
		)

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
