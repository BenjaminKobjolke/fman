"""
The worker rows a ProgressDialog shows while a copy runs on several workers,
and the buttons that add or remove workers.

Deliberately named `*_test.py` rather than `test_*.py`, so `python build.py
test` does not discover it: it needs a QApplication of its own, and stray Qt
state is what makes that suite hang (see CLAUDE.md). Run it via
tools\\run_progress_dialog_tests.bat.
"""

from dataclasses import dataclass
from fman.impl.widgets import MainWindow, ProgressDialog
from fman.impl.workers_label import WorkersLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QApplication, QWidget
from unittest import TestCase

class WorkersLabelTest(TestCase):
	def test_dialog_matches_hidden_main_window_title_bar(self):
		dialog = QWidget()
		MainWindow._match_title_bar(_FakeMainWindow(False), dialog)
		self.assertTrue(dialog.windowFlags() & Qt.FramelessWindowHint)
	def test_dialog_keeps_title_bar_when_main_window_title_bar_is_visible(self):
		dialog = QWidget()
		MainWindow._match_title_bar(_FakeMainWindow(True), dialog)
		self.assertFalse(dialog.windowFlags() & Qt.FramelessWindowHint)
	def test_rows_show_title_and_percentage(self):
		label = self._label(
			_Worker(1, 'Downloading a.jpg', progress=45, size=100), _Worker(2)
		)
		self.assertEqual('#1\n#2', label._ids.text())
		self.assertEqual('45%\n', label._percents.text())
		self.assertEqual('Downloading a.jpg\n(idle)', label._titles.text())
	def test_unknown_size_shows_no_percentage(self):
		label = self._label(_Worker(1, 'Copying a', size=0))
		self.assertEqual('', label._percents.text())
		self.assertEqual('Copying a', label._titles.text())
	def test_retiring_worker_is_marked(self):
		label = self._label(
			_Worker(1, 'Copying a'), _Worker(3, 'Copying b', retiring=True)
		)
		self.assertEqual(
			'Copying a\nCopying b  (finishing)', label._titles.text()
		)
		self.assertEqual('Threads: 1', label._count.text())
	def test_shows_file_count(self):
		workers = _FakeWorkers(_Worker(1))
		workers.file_counts = (3, 5)
		label = WorkersLabel(workers)
		self.assertEqual('3 / 5', label._files.text())
	def test_buttons_add_and_remove_workers(self):
		workers = _FakeWorkers(_Worker(1), _Worker(2))
		label = WorkersLabel(workers)
		label._add.click()
		label._remove.click()
		self.assertEqual(['add', 'remove'], workers.calls)
	def test_buttons_follow_what_workers_allow(self):
		workers = _FakeWorkers(_Worker(1))
		workers.removable = False
		label = WorkersLabel(workers)
		self.assertFalse(label._remove.isEnabled())
		self.assertTrue(label._add.isEnabled())
	def test_refresh_reports_a_changed_row_count(self):
		workers = _FakeWorkers(_Worker(1), _Worker(2))
		label = WorkersLabel(workers)
		self.assertFalse(label.refresh(''))
		workers.workers.pop()
		self.assertTrue(label.refresh(''))
	def test_progress_dialog_shows_its_text_in_the_workers_label(self):
		dialog = ProgressDialog(None, 'Copying', 100, QPalette())
		dialog.show_workers(_FakeWorkers(_Worker(1)))
		dialog.set_text('Copying 3 files')
		dialog._update()
		self.assertEqual('Copying 3 files', dialog._workers_label._text.text())
	def test_cancel_disables_the_cancel_button_not_the_worker_buttons(self):
		dialog = ProgressDialog(None, 'Copying', 100, QPalette())
		dialog.show_workers(_FakeWorkers(_Worker(1), _Worker(2)))
		dialog.request_cancel()
		self.assertFalse(dialog._cancel_button.isEnabled())
		self.assertTrue(dialog._workers_label._add.isEnabled())
		self.assertTrue(dialog._workers_label._remove.isEnabled())
	def _label(self, *workers):
		result = WorkersLabel(_FakeWorkers(*workers))
		result.refresh('')
		return result
	@classmethod
	def setUpClass(cls):
		# One QApplication per process; Qt refuses a second one.
		cls.app = QApplication.instance() or QApplication([])

@dataclass
class _Worker:
	id: int
	title: str = ''
	progress: int = 0
	size: int = 0
	retiring: bool = False

class _FakeWorkers:
	def __init__(self, *workers):
		self.workers = list(workers)
		self.calls = []
		self.removable = True
		self.file_counts = (0, 0)
	def snapshot(self):
		return list(self.workers)
	def add(self):
		self.calls.append('add')
	def remove(self):
		self.calls.append('remove')
	def can_add(self):
		return True
	def can_remove(self):
		return self.removable
	def counts(self):
		return self.file_counts

class _FakeMainWindow:
	def __init__(self, title_bar_visible):
		self._title_bar_visible = title_bar_visible
	def is_title_bar_visible(self):
		return self._title_bar_visible
