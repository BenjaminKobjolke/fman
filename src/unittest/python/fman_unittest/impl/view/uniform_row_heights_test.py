"""
UniformRowHeights hands its one row height to the vertical header.

The file list's vertical header is in Fixed mode: in ResizeToContents, Qt
re-measured every row whenever a batch of rows finished loading, which stalled
the GUI thread in directories with tens of thousands of entries. A Fixed header
never asks the view for a row's height, so the view has to tell it.

Deliberately named `*_test.py` rather than `test_*.py`, so `python build.py
test` does not discover it: it needs a QApplication of its own, and stray Qt
state is what makes that suite hang (see CLAUDE.md). Run it via
tools\\run_view_tests.bat.
"""

from fman.impl.view.uniform_row_heights import UniformRowHeights
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QApplication
from unittest import TestCase

class UniformRowHeightsTest(TestCase):
	def test_header_gets_the_row_height(self):
		row_height = self._view.get_row_height()
		self.assertEqual(row_height, self._section_size())
	def test_header_follows_a_bigger_icon_size(self):
		before = self._view.get_row_height()
		self._view.setIconSize(QSize(before * 4, before * 4))
		self.assertGreater(self._section_size(), before)
		self.assertEqual(self._view.get_row_height(), self._section_size())
	def _section_size(self):
		return self._view.verticalHeader().defaultSectionSize()
	def setUp(self):
		super().setUp()
		self._view = UniformRowHeights()
		# As FileListView does. Qt's own minimum is taller than a row:
		self._view.verticalHeader().setMinimumSectionSize(0)
		self._view.setModel(QStandardItemModel(3, 2))
		self.addCleanup(self._view.deleteLater)
	@classmethod
	def setUpClass(cls):
		# One QApplication per process; Qt refuses a second one.
		cls.app = QApplication.instance() or QApplication([])
