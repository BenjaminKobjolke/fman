"""
The worker rows a ProgressDialog shows while a copy runs on several workers,
and the buttons that add or remove workers.

Deliberately named `*_test.py` rather than `test_*.py`, so `python build.py
test` does not discover it: it needs a QApplication of its own, and stray Qt
state is what makes that suite hang (see CLAUDE.md). Run it via
tools\\run_progress_dialog_tests.bat.
"""

from dataclasses import dataclass
from fman.impl.widgets import ProgressDialog
from fman.impl.workers_label import WorkersLabel
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QApplication
from unittest import TestCase

class WorkersLabelTest(TestCase):
	def test_rows_show_title_and_percentage(self):
		label = self._label(
			_Worker(1, 'Downloading a.jpg', progress=45, size=100), _Worker(2)
		)
		self.assertEqual(
			'#1  Downloading a.jpg  45%\n#2  (idle)', label._rows.text()
		)
	def test_unknown_size_shows_no_percentage(self):
		label = self._label(_Worker(1, 'Copying a', size=0))
		self.assertEqual('#1  Copying a', label._rows.text())
	def test_retiring_worker_is_marked(self):
		label = self._label(
			_Worker(1, 'Copying a'), _Worker(3, 'Copying b', retiring=True)
		)
		self.assertEqual(
			'#1  Copying a\n#3  Copying b  (finishing)', label._rows.text()
		)
		self.assertEqual('Threads: 1', label._count.text())
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
