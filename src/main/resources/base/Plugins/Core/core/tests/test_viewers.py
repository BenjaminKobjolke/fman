"""
Which of the three built-in viewers claims which file, and the local-file
guard in front of them. This is the half of "View file" that used to be the
if/elif chain in core/commands/__init__.py; the other half (validation,
which pane, focus) is in tests/commands/test_opening.py.
"""
from core.viewers import ImageViewer, TextViewer, VideoViewer, viewer_for
from fman.url import as_url
from tempfile import NamedTemporaryFile
from unittest import TestCase
from unittest.mock import patch

import os

def _temp_file(test_case, data):
	f = NamedTemporaryFile(delete=False, suffix='.dat')
	try:
		f.write(data)
	finally:
		f.close()
	test_case.addCleanup(os.remove, f.name)
	return as_url(f.name)

class BuiltinViewerMatchesTest(TestCase):

	def test_image_claims_image_extensions(self):
		self.assertTrue(ImageViewer().matches('file:///a/b.png'))
		self.assertTrue(ImageViewer().matches('file:///a/B.JPEG'))
		self.assertFalse(ImageViewer().matches('file:///a/b.txt'))

	def test_video_claims_video_extensions(self):
		self.assertTrue(VideoViewer().matches('file:///a/b.mp4'))
		self.assertFalse(VideoViewer().matches('file:///a/b.png'))

	def test_text_claims_anything_that_sniffs_as_text(self):
		url = _temp_file(self, b'hello world')
		self.assertTrue(TextViewer().matches(url))

	def test_text_refuses_a_binary(self):
		# A NUL byte is what tells the text viewer it would garble the file.
		url = _temp_file(self, b'MZ\x00\x00binary stuff')
		self.assertFalse(TextViewer().matches(url))

	def test_text_sits_below_the_others_so_plugins_get_first_refusal(self):
		# is_text_file sniffs rather than matching an extension, so without
		# this a plugin claiming e.g. .md would never be reached.
		self.assertLess(TextViewer.priority, ImageViewer.priority)
		self.assertLess(TextViewer.priority, VideoViewer.priority)

	def test_the_three_names_are_the_stored_categories(self):
		# These are also the Core Settings.json keys
		# ('<name>_viewer_advance_same_type'), so renaming one silently
		# resets that setting for every user.
		self.assertEqual(
			['image', 'text', 'video'],
			sorted(v.name for v in (ImageViewer, TextViewer, VideoViewer))
		)

class ViewerForTest(TestCase):

	"""
	The guard the built-in viewers rely on: TextViewer.matches would try to
	read a directory, and an extension match inside a zip:// url would open a
	viewer on a file the local viewers cannot read.
	"""

	def test_delegates_to_the_registry_for_a_local_file(self):
		viewer = object()
		with patch('core.viewers.is_dir', return_value=False), \
				patch('core.viewers.find_viewer', return_value=viewer):
			self.assertIs(viewer, viewer_for('file:///a/b.png'))

	def test_refuses_a_directory(self):
		with patch('core.viewers.is_dir', return_value=True), \
				patch('core.viewers.find_viewer') as find_viewer:
			self.assertIsNone(viewer_for('file:///a/b'))
		find_viewer.assert_not_called()

	def test_refuses_a_non_local_url(self):
		with patch('core.viewers.find_viewer') as find_viewer:
			self.assertIsNone(viewer_for('zip:///a/b.zip/c.png'))
		find_viewer.assert_not_called()

	def test_checks_the_scheme_before_touching_the_file_system(self):
		# is_dir on a non-local url would go through the plugin's file system.
		with patch('core.viewers.is_dir') as is_dir:
			viewer_for('zip:///a/b.zip/c.png')
		is_dir.assert_not_called()
