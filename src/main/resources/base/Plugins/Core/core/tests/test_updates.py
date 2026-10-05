from core.updates import UpdateStatus, check_for_update, installed_label
from fman import FMAN_VERSION, links
from unittest import TestCase
from unittest.mock import patch


class UpdateStatusTest(TestCase):
	def test_only_newer_releases_are_updates(self):
		for installed, latest, expected in (
			('1.7.13_2', '1.7.13_3', True),
			('1.7.13_9', '1.8.0_1', True),
			('1.7.13_3', '1.7.13_3', False),
			('1.8.0_1', '1.7.13_9', False),
		):
			with self.subTest(installed=installed, latest=latest):
				self.assertEqual(
					expected, UpdateStatus(installed, latest).update_available
				)

	def test_invalid_label_is_not_an_update(self):
		self.assertFalse(UpdateStatus('1.7.13_3', 'v1.8.0').update_available)


class CheckForUpdateTest(TestCase):
	def test_fetches_latest_tag_and_installed_notes(self):
		with patch('core.updates.GitHubRepo') as repo, patch(
			'core.updates.list_bundled_releases', return_value=[
				('1.7.13', 2, 'notes')
			]
		):
			repo.fetch.return_value.get_latest_release.return_value = '1.7.13_3'
			status = check_for_update()
			repo.fetch.assert_called_once_with(links.GITHUB_REPO)
			self.assertEqual(('1.7.13_2', '1.7.13_3'), tuple(status))

	def test_rejects_unexpected_tag(self):
		with patch('core.updates.GitHubRepo') as repo:
			repo.fetch.return_value.get_latest_release.return_value = 'v1.7.13'
			with self.assertRaises(ValueError):
				check_for_update()

	def test_falls_back_when_notes_are_absent(self):
		with patch('core.updates.list_bundled_releases', return_value=[]):
			self.assertEqual(FMAN_VERSION + '_0', installed_label())
