"""Tests for Robocopy progress and completion reporting."""

from unittest import TestCase
from unittest.mock import Mock, patch

from robocopy_plugin.jobs import Job, Plan, Source
from robocopy_plugin.settings import Settings
from robocopy_plugin.transfer import Transfer


class TransferTest(TestCase):
	def _plan(self, move=False, settings=None):
		entry = Source(r'C:\src\file.txt', 'file.txt', False, (1, 2, 3))
		job = Job(r'C:\src', r'C:\dst', (entry,), ('file.txt',))
		return Plan(
			r'C:\src', r'C:\dst', (1, 2, 3), (job,), settings or Settings(), move
		)

	@patch('robocopy_plugin.transfer.windows.run', return_value=(1, 'copied'))
	@patch('robocopy_plugin.transfer.planner.recheck')
	def test_updates_progress_and_reports_success(self, _recheck, _run):
		transfer = Transfer('Copy with robocopy', self._plan(), None, 'robocopy.exe')
		with patch.object(transfer, 'set_text') as set_text, \
				patch.object(transfer, 'set_progress') as set_progress, \
				patch.object(transfer, 'show_alert') as show_alert, \
				patch('robocopy_plugin.transfer.fman.show_status_message') as status:
			transfer()
		self.assertTrue(set_text.called)
		set_progress.assert_called_with(1)
		show_alert.assert_not_called()
		self.assertIn('Robocopy copy', status.call_args.args[0])

	@patch('robocopy_plugin.transfer.windows.run', return_value=(1, 'copied'))
	@patch('robocopy_plugin.transfer.planner.recheck')
	def test_opens_log_after_finishing_it(self, _recheck, _run):
		settings = Settings(log_enabled=True, open_log_on_finish=True)
		transfer = Transfer(
			'Copy with robocopy', self._plan(settings=settings), 'transfer.log',
			'robocopy.exe'
		)
		events = []
		with patch('robocopy_plugin.transfer.logs.TransferLog') as log_class, \
				patch('robocopy_plugin.transfer.os.startfile') as startfile, \
				patch('robocopy_plugin.transfer.fman.show_status_message'):
			log_class.return_value.finish.side_effect = lambda _summary: events.append(
				'finish'
			)
			startfile.side_effect = lambda _path: events.append('open')
			transfer()

		self.assertEqual(events, ['finish', 'open'])

	@patch('robocopy_plugin.transfer.windows.run', return_value=(16, 'failure details'))
	@patch('robocopy_plugin.transfer.planner.recheck')
	def test_reports_failure_output(self, _recheck, _run):
		transfer = Transfer(
			'Move with robocopy', self._plan(True), None, 'robocopy.exe'
		)
		with patch.object(transfer, 'show_alert') as show_alert, \
				patch('robocopy_plugin.transfer.fman.show_status_message'):
			transfer()
		self.assertIn('failure details', show_alert.call_args.args[0])

	@patch('robocopy_plugin.transfer.windows.run', return_value=(1, ''))
	@patch('robocopy_plugin.transfer.planner.recheck')
	def test_cancel_kills_operation_and_keeps_partial_change_message(
			self, _recheck, run
	):
		transfer = Transfer('Copy with robocopy', self._plan(), None, 'robocopy.exe')
		def cancel_during_process(*_args, check, **_kwargs):
			check()
			check()
			return 1, ''
		run.side_effect = cancel_during_process
		transfer.check_canceled = Mock(side_effect=[None, transfer.Canceled()])
		with patch.object(transfer, 'show_alert') as show_alert:
			transfer()
		show_alert.assert_called_once()
		self.assertIn('partial', show_alert.call_args.args[0].lower())
