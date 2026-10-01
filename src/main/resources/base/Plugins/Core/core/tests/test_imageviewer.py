import os
import struct
from tempfile import TemporaryDirectory

from core.imageviewer import IMAGE_EXTENSIONS, is_image, load_oriented_image
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage
from unittest import TestCase


def _jpeg_with_orientation(path, orientation):
	# Qt's JPEG writer rotates pixels instead of writing the EXIF tag.
	image = QImage(20, 10, QImage.Format_RGB32)
	image.fill(Qt.red)
	image.save(path, 'JPG')
	tiff = b'MM\x00\x2a' + struct.pack('>IH', 8, 1) \
		+ struct.pack('>HHIHH', 0x0112, 3, 1, orientation, 0) \
		+ struct.pack('>I', 0)
	payload = b'Exif\x00\x00' + tiff
	segment = b'\xff\xe1' + struct.pack('>H', len(payload) + 2) + payload
	with open(path, 'rb') as jpeg_file:
		jpeg = jpeg_file.read()
	with open(path, 'wb') as jpeg_file:
		jpeg_file.write(jpeg[:2] + segment + jpeg[2:])


class LoadOrientedImageTest(TestCase):
	def test_applies_exif_rotation(self):
		with TemporaryDirectory() as directory:
			path = os.path.join(directory, 'portrait.jpg')
			_jpeg_with_orientation(path, 6)
			image = load_oriented_image(path)
			self.assertEqual((image.width(), image.height()), (10, 20))

	def test_leaves_image_without_rotation_untouched(self):
		with TemporaryDirectory() as directory:
			path = os.path.join(directory, 'landscape.jpg')
			_jpeg_with_orientation(path, 1)
			image = load_oriented_image(path)
			self.assertEqual((image.width(), image.height()), (20, 10))

	def test_missing_file_gives_null_image(self):
		with TemporaryDirectory() as directory:
			path = os.path.join(directory, 'missing.jpg')
			self.assertTrue(load_oriented_image(path).isNull())

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
