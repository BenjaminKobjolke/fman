from core.imageviewer import IMAGE_EXTENSIONS, is_image
from unittest import TestCase

class IsImageTest(TestCase):
	def test_matches_every_known_image_extension(self):
		for ext in IMAGE_EXTENSIONS:
			self.assertTrue(is_image('file:///a/b/c%s' % ext))

	def test_case_insensitive(self):
		self.assertTrue(is_image('file:///a/b/c.PNG'))

	def test_non_image_extension_is_rejected(self):
		self.assertFalse(is_image('file:///a/b/c.txt'))

	def test_no_extension_is_rejected(self):
		self.assertFalse(is_image('file:///a/b/c'))
