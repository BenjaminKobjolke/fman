from core.commands.pack import _suggest_archive_name
from unittest import TestCase

class SuggestArchiveNameTest(TestCase):

	"""
	The name Pack suggests when several files are chosen: the pane's directory.
	A drive root has no directory name - 'C:.zip' is not a valid file name.
	"""

	def test_drive_root(self):
		self.assertEqual('C.zip', _suggest_archive_name('file://C:'))
	def test_drive_root_with_trailing_slash(self):
		self.assertEqual('C.zip', _suggest_archive_name('file://C:/'))
	def test_directory(self):
		self.assertEqual('reports.zip', _suggest_archive_name('file://C:/reports'))
	def test_directory_with_trailing_slash(self):
		self.assertEqual(
			'reports.zip', _suggest_archive_name('file://C:/reports/')
		)
	def test_network_share(self):
		self.assertEqual(
			'share.zip', _suggest_archive_name('file:////server/share')
		)
	def test_unix_root(self):
		self.assertEqual('archive.zip', _suggest_archive_name('file:///'))
	def test_nameless_root(self):
		self.assertEqual('archive.zip', _suggest_archive_name('drives://'))
	def test_directory_inside_archive(self):
		self.assertEqual(
			'folder.zip', _suggest_archive_name('zip://C:/source.zip/folder')
		)
