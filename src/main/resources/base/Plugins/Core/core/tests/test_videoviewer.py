from core.videoviewer import (
	VIDEO_EXTENSIONS, format_time, get_saved_mute, get_saved_volume, is_video,
	save_mute, save_volume, show_video_viewer,
)
from unittest import TestCase
from unittest.mock import MagicMock, patch

import sys

class IsVideoTest(TestCase):
	def test_matches_every_known_video_extension(self):
		for ext in VIDEO_EXTENSIONS:
			self.assertTrue(is_video('file:///a/b/c%s' % ext))

	def test_case_insensitive(self):
		self.assertTrue(is_video('file:///a/b/c.MP4'))

	def test_non_video_extension_is_rejected(self):
		self.assertFalse(is_video('file:///a/b/c.txt'))

	def test_no_extension_is_rejected(self):
		self.assertFalse(is_video('file:///a/b/c'))

class FormatTimeTest(TestCase):
	def test_zero(self):
		self.assertEqual('0:00', format_time(0))

	def test_none_is_zero(self):
		self.assertEqual('0:00', format_time(None))

	def test_negative_is_zero(self):
		self.assertEqual('0:00', format_time(-5))

	def test_minutes_and_seconds(self):
		self.assertEqual('1:12', format_time(72))

	def test_hours_minutes_and_seconds(self):
		self.assertEqual('1:01:01', format_time(3661))

class _FakeSettings:
	# Stands in for Core Settings.json - core.settings.get_setting/save_setting
	# themselves are untested elsewhere in this codebase (see
	# test_imageviewer_zoom.py, test_textviewer_zoom.py), so this fakes the
	# thin wrapper functions videoviewer.py imports rather than fman I/O.
	def __init__(self):
		self._values = {}

	def get(self, json_name, key, default=None):
		return self._values.get(key, default)

	def save(self, json_name, key, value):
		if value is None:
			self._values.pop(key, None)
		else:
			self._values[key] = value

class VolumeAndMutePersistenceTest(TestCase):
	def setUp(self):
		self._settings = _FakeSettings()
		patcher_get = patch('core.videoviewer.get_setting', self._settings.get)
		patcher_save = patch('core.videoviewer.save_setting', self._settings.save)
		patcher_get.start()
		patcher_save.start()
		self.addCleanup(patcher_get.stop)
		self.addCleanup(patcher_save.stop)

	def test_volume_round_trips(self):
		save_volume(50)
		self.assertEqual(50, get_saved_volume())

	def test_volume_defaults_to_none_when_nothing_saved(self):
		self.assertIsNone(get_saved_volume())

	def test_mute_defaults_to_false_when_nothing_saved(self):
		self.assertIs(False, get_saved_mute())

	def test_mute_round_trips_true(self):
		save_mute(True)
		self.assertIs(True, get_saved_mute())

class ShowVideoViewerTest(TestCase):
	def test_missing_mpv_module_shows_alert(self):
		# sys.modules[name] = None makes `import name` raise ImportError. That
		# reproduces the frozen build, where the Core plugin ships as resource
		# data so PyInstaller never sees `import mpv` (see the mpv entry in
		# src/build/settings/base.json's hidden_imports).
		with patch.dict(sys.modules, {'mpv': None}), 				patch('core.videoviewer.ensure_libmpv_on_path'), 				patch('core.videoviewer.show_alert') as alert, 				patch('core.videoviewer._open_video_view') as open_view:
			show_video_viewer(MagicMock(), 'file:///a/b/c.mp4')
		self.assertEqual(1, alert.call_count)
		open_view.assert_not_called()
