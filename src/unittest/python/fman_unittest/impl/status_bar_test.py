"""A long status message must not set the main window's minimum width."""

from fman.impl.widgets import MainWindow
from PyQt5.QtWidgets import QApplication
from unittest import TestCase


class StatusBarTest(TestCase):
	@classmethod
	def setUpClass(cls):
		cls.app = QApplication.instance() or QApplication([])

	def test_long_message_does_not_widen_the_minimum_window(self):
		window = MainWindow(None, [], None, None, None, None)
		self.addCleanup(window.deleteLater)
		window.ensurePolished()
		window.show_status_message('Ready.')
		window._status_bar.layout().activate()
		minimum_width = window.minimumSizeHint().width()

		window.show_status_message('x' * 500)
		window._status_bar.layout().activate()

		self.assertEqual(minimum_width, window.minimumSizeHint().width())
