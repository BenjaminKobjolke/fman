"""FileListView selection tests use a QApplication of their own."""

from fman.impl.view import FileListView
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QApplication
from unittest import TestCase
from unittest.mock import Mock


class SelectionModel(QStandardItemModel):
	sort_order_changed = pyqtSignal(int, int)
	transaction_ended = pyqtSignal()

	def __init__(self):
		super().__init__(5, 2)

	def find(self, url):
		try:
			row = {'first': 0, 'second': 1, 'third': 2, 'fourth': 3, 'fifth': 4}[url]
			return self.index(row, 0)
		except KeyError:
			raise ValueError(url)


class FileListSelectionTest(TestCase):
	@classmethod
	def setUpClass(cls):
		cls.app = QApplication.instance() or QApplication([])

	def setUp(self):
		self.view = FileListView(None, lambda *_: [])
		self.view.setModel(SelectionModel())
		self.addCleanup(self.view.deleteLater)

	def test_non_contiguous_selection_emits_once(self):
		changed = Mock()
		self.view.selectionModel().selectionChanged.connect(changed)
		self.view.select(['first', 'third', 'unknown', 'fifth'], ignore_errors=True)
		self.assertEqual(
			[0, 2, 4],
			sorted(index.row() for index in self.view.selectionModel().selectedRows())
		)
		changed.assert_called_once()

	def test_unknown_url_keeps_earlier_selection(self):
		with self.assertRaises(ValueError):
			self.view.select(['first', 'unknown'])
		self.assertEqual(
			[0], [index.row() for index in self.view.selectionModel().selectedRows()]
		)

	def test_string_is_rejected(self):
		with self.assertRaises(ValueError):
			self.view.select('first')
