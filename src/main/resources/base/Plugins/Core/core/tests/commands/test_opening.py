from core.commands.opening import OpenOrView, ViewFile, ViewFileInOtherPane
from core.tests.commands import FakePane, FakeWindow
from fman.url import as_url
from tempfile import NamedTemporaryFile
from unittest import TestCase
from unittest.mock import MagicMock, patch

import os

def _write_temp_file(test_case, data):
	f = NamedTemporaryFile(delete=False)
	try:
		f.write(data)
	finally:
		f.close()
	test_case.addCleanup(os.remove, f.name)
	return f.name

class OpenOrViewTest(TestCase):
	def test_dispatches_by_cursor_target(self):
		cases = (
			# label, is_dir, is_viewable, expected command
			('directory', True, True, 'open'),
			('file', False, True, 'view_file'),
			('binary', False, False, 'open'),
			(None, False, True, 'open'),
		)
		for label, cursor_is_dir, viewable, expected_command in cases:
			with self.subTest(label=label, viewable=viewable):
				url = 'file://' + label if label else None
				pane = FakePane(url=url)
				with patch(
						'core.commands.opening.is_dir',
						return_value=cursor_is_dir
				), patch(
						'core.commands.opening._is_viewable',
						return_value=viewable
				):
					OpenOrView(pane)()
				self.assertEqual([expected_command], pane.commands_run)

	def test_non_local_url_falls_back_to_open(self):
		# Scheme check happens before _is_viewable, so a viewable-looking
		# remote file still can't be handed to the (local-only) viewer.
		pane = FakePane(url='http://example.com/file.txt')
		with patch('core.commands.opening.is_dir', return_value=False), \
				patch(
					'core.commands.opening._is_viewable', return_value=True
				):
			OpenOrView(pane)()
		self.assertEqual(['open'], pane.commands_run)

class _ViewerTestCase(TestCase):

	# Every test here needs the same three seams: what the file system says
	# the URL is, which viewer claims it, and whether an alert was shown.
	def setUp(self):
		super().setUp()
		self.viewer = MagicMock()
		self.is_dir = self._patch('is_dir', return_value=False)
		self.viewer_for = self._patch('viewer_for', return_value=self.viewer)
		self.show_alert = self._patch('show_alert')
	def _patch(self, name, **kwargs):
		patcher = patch('core.commands.opening.' + name, **kwargs)
		self.addCleanup(patcher.stop)
		return patcher.start()

# Which viewer claims which file now lives in the registry, and is covered by
# core/tests/test_viewers.py. These tests are about the commands' own job:
# validate, pick the target pane, decide focus, alert when nothing handles it.
class ViewFileTest(_ViewerTestCase):
	def test_viewable_file_opens_its_viewer(self):
		path = _write_temp_file(self, b'hello world')
		ViewFile(FakePane(url=as_url(path)))()
		self.viewer.show.assert_called_once()
		self.show_alert.assert_not_called()

	def test_file_no_viewer_handles_shows_an_alert(self):
		path = _write_temp_file(self, b'MZ\x00\x00binary stuff')
		self.viewer_for.return_value = None
		ViewFile(FakePane(url=as_url(path)))()
		self.show_alert.assert_called_once()

class ViewFileInOtherPaneTest(_ViewerTestCase):
	def test_mounts_in_other_pane_without_stealing_focus(self):
		path = _write_temp_file(self, b'hello world')
		source, target = self._panes(as_url(path), None)
		ViewFileInOtherPane(source)()
		# Mounted into the OTHER pane, and told not to grab keyboard focus so
		# browsing stays in the source pane.
		self.assertIs(target, self.viewer.show.call_args[0][0])
		self.assertFalse(self.viewer.show.call_args.kwargs['focus_view'])
		self.show_alert.assert_not_called()

	def test_single_pane_views_in_place_and_takes_focus(self):
		path = _write_temp_file(self, b'hello world')
		only, = self._panes(as_url(path))
		ViewFileInOtherPane(only)()
		self.assertIs(only, self.viewer.show.call_args[0][0])
		self.assertTrue(self.viewer.show.call_args.kwargs['focus_view'])
		self.show_alert.assert_not_called()

	def test_validation_failure_mounts_nothing(self):
		source, target = self._panes(None, None)  # no file selected
		ViewFileInOtherPane(source)()
		self.show_alert.assert_called_once()
		self.viewer.show.assert_not_called()

	def _panes(self, *urls):
		window = FakeWindow()
		window._panes = [FakePane(window, url) for url in urls]
		return window._panes
