from core.commands.editor import _find_extension_start
from unittest import TestCase

class FindExtensionStartTest(TestCase):
	def test_no_extension(self):
		self.assertIsNone(_find_extension_start('File'))
	def test_normal_extension(self):
		self.assertEqual(4, _find_extension_start('test.zip'))
	def test_tar_xz(self):
		self.assertEqual(7, _find_extension_start('archive.tar.xz'))
	def test_tar_gz(self):
		self.assertEqual(7, _find_extension_start('archive.tar.gz'))
