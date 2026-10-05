from core.commands.updates import CheckForUpdates
from core.updates import UpdateStatus
from fman import NO, YES, links
from unittest import TestCase
from unittest.mock import patch
from urllib.error import URLError


class CheckForUpdatesTest(TestCase):
	def setUp(self):
		self.patches = {}
		for name in (
			'check_for_update', 'show_alert', 'load_json', 'save_json',
			'QDesktopServices', 'show_status_message', 'clear_status_message'
		):
			p = patch('core.commands.updates.' + name)
			self.patches[name] = p.start()
			self.addCleanup(p.stop)
		self.patches['load_json'].return_value = {}
		self.patches['check_for_update'].return_value = UpdateStatus(
			'1.7.13_2', '1.7.13_3'
		)

	def test_alias(self):
		self.assertEqual(('Check for updates',), CheckForUpdates.aliases)

	def test_manual_yes_opens_release_page(self):
		self.patches['show_alert'].return_value = YES
		CheckForUpdates(None)()
		url = self.patches['QDesktopServices'].openUrl.call_args.args[0]
		self.assertEqual(links.RELEASES, url.toString())
		self.patches['clear_status_message'].assert_called_once()

	def test_manual_no_does_not_open_page(self):
		self.patches['show_alert'].return_value = NO
		CheckForUpdates(None)()
		self.patches['QDesktopServices'].openUrl.assert_not_called()

	def test_manual_up_to_date_reports_result(self):
		self.patches['check_for_update'].return_value = UpdateStatus(
			'1.7.13_3', '1.7.13_3'
		)
		CheckForUpdates(None)()
		self.patches['show_alert'].assert_called_once_with(
			'fman 1.7.13_3 is up to date.'
		)

	def test_manual_failures_report_error(self):
		for error in (URLError('offline'), ValueError('bad tag'), KeyError('tag')):
			with self.subTest(error=error):
				self.patches['show_alert'].reset_mock()
				self.patches['check_for_update'].side_effect = error
				CheckForUpdates(None)()
				self.assertIn(
					'Could not check for updates',
					self.patches['show_alert'].call_args.args[0]
				)

	def test_silent_no_update_or_error_is_quiet(self):
		self.patches['check_for_update'].return_value = UpdateStatus(
			'1.7.13_3', '1.7.13_3'
		)
		CheckForUpdates(None)(silent=True)
		self.patches['check_for_update'].side_effect = URLError('offline')
		CheckForUpdates(None)(silent=True)
		self.patches['show_alert'].assert_not_called()

	def test_silent_new_update_announces_once(self):
		CheckForUpdates(None)(silent=True)
		self.patches['show_alert'].assert_called_once()
		self.patches['save_json'].assert_called_once_with('Update Check.json')
		self.assertEqual(
			'1.7.13_3', self.patches['load_json'].return_value['announced']
		)
		self.patches['show_alert'].reset_mock()
		CheckForUpdates(None)(silent=True)
		self.patches['show_alert'].assert_not_called()

	def test_manual_ignores_prior_announcement(self):
		self.patches['load_json'].return_value = {'announced': '1.7.13_3'}
		CheckForUpdates(None)()
		self.patches['show_alert'].assert_called_once()
