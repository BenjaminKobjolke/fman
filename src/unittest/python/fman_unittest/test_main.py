import unittest
from unittest.mock import Mock, patch

from fman import main


class SkipInterpreterTeardownTest(unittest.TestCase):
	def test_flushes_streams_and_exits_with_app_code(self):
		stdout, stderr = Mock(), Mock()
		exit_mock, shutdown_mock = self._run_with_streams(stdout, stderr)
		shutdown_mock.assert_called_once_with()
		stdout.flush.assert_called_once_with()
		stderr.flush.assert_called_once_with()
		exit_mock.assert_called_once_with(3)

	def test_exits_when_output_streams_are_absent(self):
		exit_mock, shutdown_mock = self._run_with_streams(None, None)
		shutdown_mock.assert_called_once_with()
		exit_mock.assert_called_once_with(3)

	def test_exits_when_a_stream_flush_fails(self):
		# A closed stream raises ValueError, a broken output pipe OSError.
		for error in (ValueError('closed file'), OSError('broken pipe')):
			for failing in ('stdout', 'stderr'):
				with self.subTest(error=error, failing=failing):
					streams = {'stdout': Mock(), 'stderr': Mock()}
					streams[failing].flush.side_effect = error
					exit_mock, _ = self._run_with_streams(**streams)
					for stream in streams.values():
						stream.flush.assert_called_once_with()
					exit_mock.assert_called_once_with(3)

	def _run_with_streams(self, stdout, stderr):
		original_code = main._skip_interpreter_teardown.exit_code
		try:
			main._skip_interpreter_teardown.exit_code = 3
			with patch.object(main.os, '_exit') as exit_mock, \
				 patch.object(main.logging, 'shutdown') as shutdown_mock, \
				 patch.object(main.sys, 'stdout', stdout), \
				 patch.object(main.sys, 'stderr', stderr):
				main._skip_interpreter_teardown()
		finally:
			main._skip_interpreter_teardown.exit_code = original_code
		return exit_mock, shutdown_mock
