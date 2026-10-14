import sys
from unittest import TestCase, skipUnless
from unittest.mock import patch

from fbs_runtime.platform import is_windows

from core.commands.drag_to_app import (
	_DRAGDROP_S_CANCEL,
	_DRAGDROP_S_DROP,
	_S_OK,
	_Window,
	_drop_decision,
	_enumerate_windows,
	_pick_target,
)


@skipUnless(is_windows(), 'Windows-only window enumeration')
class EnumerateWindowsTest(TestCase):
	def test_enumerates_windows_without_win32process(self):
		with patch.dict(sys.modules, {'win32process': None}):
			windows = _enumerate_windows()

		self.assertTrue(windows)
		self.assertTrue(all(isinstance(window, _Window) for window in windows))
		self.assertTrue(any(window.pid > 0 for window in windows))


class PickTargetTest(TestCase):
	def test_returns_first_eligible_window_in_z_order(self):
		windows = [
			_Window(1, 10, 'own', True, False, False, False, False),
			_Window(2, 20, 'first', True, False, False, False, False),
			_Window(3, 30, 'second', True, False, False, False, False),
		]

		self.assertEqual(windows[1], _pick_target(windows, own_pid=10))

	def test_skips_ineligible_windows(self):
		windows = [
			_Window(1, 10, 'own process', True, False, False, False, False),
			_Window(2, 20, 'invisible', False, False, False, False, False),
			_Window(3, 30, 'minimized', True, True, False, False, False),
			_Window(4, 40, 'tool', True, False, True, False, False),
			_Window(5, 50, 'cloaked', True, False, False, True, False),
			_Window(6, 60, '', True, False, False, False, False),
			_Window(7, 70, 'eligible', True, False, False, False, False),
		]

		self.assertEqual(windows[-1], _pick_target(windows, own_pid=10))

	def test_returns_none_when_no_window_qualifies(self):
		windows = [
			_Window(1, 10, 'own process', True, False, False, False, False),
			_Window(2, 20, 'minimized', True, True, False, False, False),
		]

		self.assertIsNone(_pick_target(windows, own_pid=10))

	def test_prefers_normal_window_over_topmost(self):
		clock = _Window(1, 20, 'clock', True, False, False, False, True)
		thunderbird = _Window(2, 30, 'Thunderbird', True, False, False, False, False)

		self.assertEqual(thunderbird, _pick_target([clock, thunderbird], own_pid=10))

	def test_falls_back_to_topmost_when_no_normal_window(self):
		clock = _Window(1, 20, 'clock', True, False, False, False, True)

		self.assertEqual(clock, _pick_target([clock], own_pid=10))


class DropDecisionTest(TestCase):
	def test_escape_cancels(self):
		self.assertEqual(_DRAGDROP_S_CANCEL, _drop_decision(True, 0, 0))

	def test_waits_before_drop_deadline(self):
		self.assertEqual(_S_OK, _drop_decision(False, 1, 2))

	def test_drops_at_deadline(self):
		self.assertEqual(_DRAGDROP_S_DROP, _drop_decision(False, 2, 2))

	def test_escape_wins_over_elapsed_deadline(self):
		self.assertEqual(_DRAGDROP_S_CANCEL, _drop_decision(True, 2, 1))
