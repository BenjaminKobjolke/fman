from core.commands.release_notes import ShowReleaseNotes
from unittest import TestCase

class ShowReleaseNotesTest(TestCase):
	def test_has_expected_aliases(self):
		self.assertIn('Release Notes', ShowReleaseNotes.aliases)

	def test_hidden_when_no_releases_found(self):
		command = ShowReleaseNotes.__new__(ShowReleaseNotes)
		command._list_releases = lambda: []
		self.assertFalse(command.is_visible())

	def test_visible_when_releases_found(self):
		command = ShowReleaseNotes.__new__(ShowReleaseNotes)
		command._list_releases = lambda: [('1.7.5', 1, '/fake/1.7.5_1')]
		self.assertTrue(command.is_visible())
