"""
BuildShutdownFilter: how fman answers tools\\close_running_fman.ps1.

Deliberately named `*_test.py` rather than `test_*.py`, so `python build.py
test` does not discover it: it needs a QApplication of its own, and stray Qt
state is what makes that suite hang (see CLAUDE.md). Run it via
tools\\run_build_shutdown_tests.bat.
"""

from ctypes import addressof, windll
from ctypes.wintypes import MSG
from fman.impl.build_shutdown import BuildShutdownFilter, MESSAGE_NAME
from PyQt5.QtWidgets import QApplication, QWidget
from time import time
from unittest import TestCase

EVENT_TYPE = b'windows_generic_MSG'
WM_CLOSE = 0x10

class BuildShutdownFilterTest(TestCase):
	def test_other_messages_are_left_to_qt(self):
		result = self._send(WM_CLOSE, 1)
		self.assertEqual((False, 0), result)
		self.assertEqual([], self._main_window.dialogs)
	def test_countdown_ends_in_quit(self):
		self.assertEqual((True, 1), self._send(self._message_id, 1))
		self._wait_for_countdown()
		self.assertEqual(1, len(self._main_window.dialogs))
		self.assertEqual(1, self._quit_calls)
	def test_cancel_keeps_fman_running(self):
		self._main_window.cancel = True
		self.assertEqual((True, 1), self._send(self._message_id, 5))
		self._wait_for_countdown()
		self.assertEqual(1, len(self._main_window.dialogs))
		self.assertEqual(0, self._quit_calls)
	def setUp(self):
		super().setUp()
		self._app = QApplication.instance() or QApplication([])
		self._main_window = StubMainWindow()
		self._quit_calls = 0
		self._filter = BuildShutdownFilter(self._main_window, self._quit)
		self._message_id = windll.user32.RegisterWindowMessageW(MESSAGE_NAME)
	def _quit(self):
		self._quit_calls += 1
	def _send(self, message_id, seconds):
		msg = MSG(message=message_id, wParam=seconds)
		return self._filter.nativeEventFilter(EVENT_TYPE, addressof(msg))
	def _wait_for_countdown(self):
		# The filter only schedules the countdown; the event loop shows it.
		_process_events_until(
			lambda: self._main_window.dialogs and
				not self._filter.is_counting_down()
		)
		self.assertFalse(self._filter.is_counting_down())

class StubMainWindow(QWidget):
	"""
	Plays the countdown without showing it: show() aborts under the offscreen
	platform (see messagebox_layout_test.py).
	"""
	def __init__(self):
		super().__init__()
		self.dialogs = []
		self.cancel = False
	def exec_dialog(self, dialog):
		self.dialogs.append(dialog)
		results = []
		dialog.finished.connect(results.append)
		if self.cancel:
			dialog.button(dialog.Cancel).click()
		_process_events_until(lambda: results)
		return results[0]

def _process_events_until(condition, timeout_secs=10):
	deadline = time() + timeout_secs
	while not condition() and time() < deadline:
		QApplication.processEvents()
