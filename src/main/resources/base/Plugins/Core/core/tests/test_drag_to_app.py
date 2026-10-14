from unittest import TestCase

from core.commands.drag_to_app import _pick_target


class PickTargetTest(TestCase):
	def test_returns_first_eligible_window_in_z_order(self):
		windows = [
			(1, 10, 'own', True, False, False, False),
			(2, 20, 'first', True, False, False, False),
			(3, 30, 'second', True, False, False, False),
		]

		self.assertEqual(windows[1], _pick_target(windows, own_pid=10))

	def test_skips_ineligible_windows(self):
		windows = [
			(1, 10, 'own process', True, False, False, False),
			(2, 20, 'invisible', False, False, False, False),
			(3, 30, 'minimized', True, True, False, False),
			(4, 40, 'tool', True, False, True, False),
			(5, 50, 'cloaked', True, False, False, True),
			(6, 60, '', True, False, False, False),
			(7, 70, 'eligible', True, False, False, False),
		]

		self.assertEqual(windows[-1], _pick_target(windows, own_pid=10))

	def test_returns_none_when_no_window_qualifies(self):
		windows = [
			(1, 10, 'own process', True, False, False, False),
			(2, 20, 'minimized', True, True, False, False),
		]

		self.assertIsNone(_pick_target(windows, own_pid=10))
