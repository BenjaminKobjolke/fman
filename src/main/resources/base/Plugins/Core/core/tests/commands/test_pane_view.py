from core.commands.pane_view import ShowAllPanes, ShowOnlyActivePane, \
	SwitchPanes
from core.tests.commands import FakeWindow
from PyQt5.QtWidgets import QApplication
from unittest import TestCase

# ShowOnlyActivePane is decorated with @run_in_main_thread, which needs a
# QApplication instance to exist (even though it never enters its event
# loop here, since the test runs on the same thread it dispatches to).
# Keep a module-level reference so it isn't garbage-collected:
_APP = QApplication.instance() or QApplication([])

class _FakeWidget:
	def __init__(self, visible=True):
		self._visible = visible
	def isVisible(self):
		return self._visible
	def setVisible(self, visible):
		self._visible = visible

class _FakePane:
	def __init__(self, window):
		self.window = window
		self._widget = _FakeWidget()
		self.focused = False
	def focus(self):
		self.focused = True

def _two_pane_window():
	window = FakeWindow()
	active, other = _FakePane(window), _FakePane(window)
	window._panes = [active, other]
	return window, active, other

class ShowOnlyActivePaneTest(TestCase):
	def test_hides_other_panes(self):
		window, active, other = _two_pane_window()
		ShowOnlyActivePane(active)()
		self.assertTrue(active._widget.isVisible())
		self.assertFalse(other._widget.isVisible())
		self.assertTrue(active.focused)
	def test_visible_only_with_multiple_panes_all_shown(self):
		window, active, other = _two_pane_window()
		self.assertTrue(ShowOnlyActivePane(active).is_visible())
		other._widget.setVisible(False)
		self.assertFalse(ShowOnlyActivePane(active).is_visible())
		window._panes = [active]
		self.assertFalse(ShowOnlyActivePane(active).is_visible())

class SwitchPanesTest(TestCase):
	def test_switches_to_visible_pane(self):
		window, active, other = _two_pane_window()
		SwitchPanes(active)()
		self.assertTrue(other.focused)
	def test_does_not_switch_to_hidden_pane(self):
		window, active, other = _two_pane_window()
		ShowOnlyActivePane(active)()
		SwitchPanes(active)()
		self.assertFalse(other.focused)

class ShowAllPanesTest(TestCase):
	def test_restores_all_panes(self):
		window, active, other = _two_pane_window()
		other._widget.setVisible(False)
		ShowAllPanes(active)()
		self.assertTrue(active._widget.isVisible())
		self.assertTrue(other._widget.isVisible())
		self.assertTrue(active.focused)
	def test_visible_only_when_a_pane_is_hidden(self):
		window, active, other = _two_pane_window()
		self.assertFalse(ShowAllPanes(active).is_visible())
		other._widget.setVisible(False)
		self.assertTrue(ShowAllPanes(active).is_visible())
