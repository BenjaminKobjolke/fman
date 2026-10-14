"""Tests for the Windows process runner without requiring a Windows host."""

import importlib
from unittest import TestCase
from unittest.mock import Mock, patch

from robocopy_plugin import windows


class OutputTailTest(TestCase):
	def test_keeps_only_the_bounded_tail(self):
		output = windows.OutputTail(5)
		output.append('abc')
		output.append('def')
		self.assertEqual('bcdef', output.text())

	def test_decodes_robocopy_unicode_output(self):
		self.assertEqual('Copied\n', windows.output_text('Copied\n'.encode('utf-16-le')))


class RunTest(TestCase):
	def _process(self, code=0):
		process = Mock()
		process.stdout.read.side_effect = ['line\n'.encode('utf-16-le'), b'']
		process.poll.return_value = code
		process.wait.return_value = code
		return process

	@patch('robocopy_plugin.windows.Popen')
	def test_captures_unicode_output_and_returns_exit_code(self, popen):
		popen.return_value = self._process(3)
		self.assertEqual((3, 'line\n'), windows.run(('robocopy.exe', 'src', 'dst')))
		self.assertEqual('robocopy.exe', popen.call_args.args[0][0])

	@patch('robocopy_plugin.windows.Popen')
	def test_cancels_the_child_when_check_raises(self, popen):
		process = self._process()
		process.poll.side_effect = [None, None, -9]
		popen.return_value = process
		checks = [0]
		def cancel():
			checks[0] += 1
			if checks[0] > 1:
				raise KeyboardInterrupt()
		with self.assertRaises(KeyboardInterrupt):
			windows.run(('robocopy.exe',), check=cancel)
		process.kill.assert_called_once_with()
		process.wait.assert_called()

	@patch('robocopy_plugin.windows.Popen')
	@patch('robocopy_plugin.windows.monotonic', return_value=10)
	def test_timeout_kills_the_child(self, _clock, popen):
		process = self._process()
		process.poll.return_value = None
		popen.return_value = process
		with patch('robocopy_plugin.windows.monotonic', side_effect=[0, 11]), \
				patch('robocopy_plugin.windows.sleep'):
			with self.assertRaises(TimeoutError):
				windows.run(('robocopy.exe',), timeout=10)
		process.kill.assert_called_once_with()


class LazyWindowsApiTest(TestCase):
	def test_plugin_import_does_not_load_windows_dlls_on_other_platforms(self):
		import robocopy_plugin
		with patch('fman.PLATFORM', 'Linux'), patch('ctypes.WinDLL', create=True) as load:
			importlib.reload(windows)
			importlib.reload(robocopy_plugin)
			load.assert_not_called()
		importlib.reload(robocopy_plugin)
