from fman.fs import Column
from fman.impl.model import Model, Cell
from fman.impl.model import model as model_module
from fman.impl.model.file_watcher import FileWatcher
from fman.impl.model.model import File, _NOT_LOADED
from fman.impl.util.qt.thread import Executor
from fman.url import basename, splitscheme
from fman_unittest.impl.model import StubFileSystem
from PyQt5.QtCore import QObject, pyqtSignal
from random import shuffle, random
from unittest import TestCase
from unittest.mock import MagicMock, patch

import random

class ExecutorTestCase(TestCase):

	"""
	Base for tests that let @run_in_main_thread methods run inline.
	"""

	def setUp(self):
		super().setUp()
		self._app = StubApp()
		self._executor_before = Executor._INSTANCE # Typically None
		Executor._INSTANCE = Executor(self._app)
	def tearDown(self):
		self._app.aboutToQuit.emit()
		Executor._INSTANCE = self._executor_before
		super().tearDown()
	def _expect_data(self, expected, message=None):
		m = self._model
		actual = [
			tuple(m.data(m.index(i, j)) for j in range(m.columnCount()))
			for i in range(m.rowCount())
		]
		self.assertEqual(expected, actual, message)

class ModelRecordFilesTest(ExecutorTestCase):
	def test_load_file(self):
		f_not_loaded = f('s://a', [c('')], False)
		self._model._record_files([f_not_loaded])
		self._expect_data([('',)])
		f_loaded = f('s://a', [c('a')])
		self._model._record_files([f_loaded])
		self._expect_data([('a',)])
	def test_remove_file(self):
		self._model._record_files([f('s://a', [c('a')])])
		self._expect_data([('a',)])
		self._model._record_files([], ['s://a'])
		self._expect_data([])
	def test_remove_two_files(self):
		self._model._record_files([
			f('s://a', [c('a', 0)]),
			f('s://b', [c('b', 1)])
		])
		self._expect_data([('a',), ('b',)])
		self._model._record_files([], ['s://a', 's://b'])
		self._expect_data([])
	def test_remove_files_gap(self):
		self._model._record_files([
			f('s://a', [c('a', 0)]),
			f('s://b', [c('b', 1)]),
			f('s://c', [c('c', 2)]),
			f('s://d', [c('d', 3)]),
		])
		self._expect_data([('a',), ('b',), ('c',), ('d',)])
		self._model._record_files([], ['s://b', 's://d'])
		self._expect_data([('a',), ('c',)])
	def test_remove_files_out_of_order(self):
		self._model._record_files([
			f('s://a', [c('a', 0)]),
			f('s://b', [c('b', 1)]),
			f('s://c', [c('c', 2)])
		])
		self._expect_data([('a',), ('b',), ('c',)])
		self._model._record_files([], ['s://c', 's://b'])
		self._expect_data([('a',)])
	def test_complex(self):
		e = f('s://e', [c('e', 4)])
		self._model._record_files([
			f('s://a', [c('a', 0)]),
			f('s://b', [c('b', 1)]),
			f('s://d', [c('d', 2)]),
			e
		])
		self._expect_data([('a',), ('b',), ('d',), ('e',)])
		# Simulate e having fallen out of the filter:
		self._model._filters.append(lambda url: url != e.url)
		self._model._record_files([
			f('s://c', [c('c', 3)]),
			f('s://a', [c('a', 5)]),
			e
		], ['s://d'])
		self._expect_data([('b',), ('c',), ('a',)])
	def test_many_moves(self):
		files = [f('s://%d' % i, [c(str(i), i)]) for i in range(5)]
		self._model._record_files(files)
		self._expect_data([(str(i),) for i in range(5)])
		order_after = [4, 0, 3, 2, 1]
		self._model._record_files(
			[f('s://%d' % j, [c(str(j), i)]) for i, j in enumerate(order_after)]
		)
		self._expect_data([(str(i),) for i in order_after])
	def test_reverse(self, num=3):
		files = [f('s://%d' % i, [c(str(i), i)]) for i in range(num)]
		self._model._record_files(files)
		self._expect_data([(str(i),) for i in range(num)])
		new_files = [
			f('s://%d' % i, [c(str(i), j)])
			for j, i in enumerate(reversed(range(num)))
		]
		self._model._record_files(new_files)
		self._expect_data([(str(i),) for i in reversed(range(num))])
	def test_move_last(self):
		files = [f('s://%d' % i, [c(str(i), i)]) for i in range(3)]
		self._model._record_files(files)
		self._expect_data([(str(i),) for i in range(3)])
		order_after = [2, 0, 1]
		self._model._record_files(
			[f('s://%d' % j, [c(str(j), i)]) for i, j in enumerate(order_after)]
		)
		self._expect_data([(str(i),) for i in order_after])
	def test_file_disappeared(self):
		files = [f('s://%d' % i, [c(str(i), i)]) for i in range(4)]
		self._model._record_files(files)
		self._expect_data([(str(i),) for i in range(4)])
		new_files = [
			f('s://3', [c('3', 0)]),
			f('s://0', [c('0', 1)]),
			f('s://2', [c('2', 2)])
		]
		self._model._record_files(new_files, disappeared=['s://1'])
		self._expect_data([('3',), ('0',), ('2',)])
	def test_random(self):
		for num in list(range(6)) + [100]:
			self._test_random(num)
			self.tearDown()
			self.setUp()
	def _test_random(self, num=3):
		to_url = lambda i: 's://%d' % i
		from_url = lambda url: int(splitscheme(url)[1])
		files = [f(to_url(i), [c(str(i), i)]) for i in range(num)]
		self._model._record_files(files)
		self._expect_data([(str(i),) for i in range(num)])
		random_state = random.getstate()
		order = list(range(num))
		shuffle(order)
		filtered_out = {i for i in order if random.random() < .2}
		filter_ = lambda url: from_url(url) not in filtered_out
		disappeared = []
		for index in range(len(order) - 1, -1, -1):
			i = order[index]
			if i not in filtered_out and random.random() < .1:
				order.pop(index)
				disappeared.append(to_url(i))
		new_files = [f(to_url(j), [c(str(j), i)]) for i, j in enumerate(order)]
		self._model._filters.append(filter_)
		self._model._record_files(new_files, disappeared)
		message = 'num was %d, random.getstate() was %r' % (num, random_state)
		self._expect_data([
			(str(i),) for i in order if i not in filtered_out
		], message)
	def setUp(self):
		super().setUp()
		self._fs = StubFileSystem({})
		self._model = Model(self._fs, 'null://', [Column()])
		self.maxDiff = None

class ModelRecordFilesDescendingTest(ExecutorTestCase):

	"""
	The same incremental updates, but in a pane sorted *descending*.

	RecordFiles places new and moved rows with bisect_left over the live row
	list. #_sorted(...) used to build that list with reverse=True, so in a
	descending pane bisect_left searched a decreasing sequence and returned
	garbage - which is how a renamed file (a rename reaches the model as
	remove + add) jumped to the bottom until the next reload.
	"""

	def test_insert_into_middle(self):
		self._record(3, 1)
		self._model._record_files([self._f(2)])
		self._expect(3, 2, 1)
	def test_insert_at_top(self):
		self._record(3, 1)
		self._model._record_files([self._f(4)])
		self._expect(4, 3, 1)
	def test_insert_at_bottom(self):
		self._record(3, 1)
		self._model._record_files([self._f(0)])
		self._expect(3, 1, 0)
	def test_rename_keeps_position(self):
		# What a rename looks like to the model: the old url disappears and a
		# new one with the same sort value appears.
		self._record(5, 3, 1)
		self._model._record_files([self._f(3, url='s://renamed')], ['s://3'])
		self._expect(5, 3, 1)
	def test_changed_sort_value_moves_row(self):
		self._record(5, 3, 1)
		# 's://5' was touched and is now the *oldest* of the three:
		self._model._record_files([self._f(0, url='s://5')])
		self._expect(3, 1, 0)
	def _record(self, *sort_values):
		self._model._record_files([self._f(i) for i in sort_values])
		self._expect(*sort_values)
	def _f(self, sort_value, url=None):
		if url is None:
			url = 's://%d' % sort_value
		return f(url, [c(str(sort_value), sort_value_desc=sort_value)])
	def _expect(self, *sort_values):
		self._expect_data([(str(i),) for i in sort_values])
	def setUp(self):
		super().setUp()
		self._model = \
			Model(StubFileSystem({}), 'null://', [Column()], ascending=False)
		self.maxDiff = None

class LoadRemainingFilesTest(ExecutorTestCase):

	"""
	A file whose stat() keeps failing yields cells identical to its unloaded
	placeholder, so RecordFiles sees no change and the row stays .is_loaded ==
	False. #_load_remaining_files(...) must still give up on it - it used to
	re-submit itself forever, hammering the FS and the GUI thread.
	"""

	def test_unloadable_row_is_attempted_once(self):
		self._add_unloadable_row('s://a')
		self._load_remaining_files()
		self._load_remaining_files()
		self.assertEqual(['s://a'], self._loaded)
	def test_reload_retries(self):
		self._add_unloadable_row('s://a')
		self._load_remaining_files()
		self._model._load_attempted.clear()
		self._load_remaining_files()
		self.assertEqual(['s://a', 's://a'], self._loaded)
	def _add_unloadable_row(self, url):
		self._model._record_files([f(url, [c('a')], is_loaded=False)])
	def _load_remaining_files(self):
		# Bypass @transaction: it submits to a worker thread that these tests
		# never start.
		Model._load_remaining_files.__wrapped__(self._model)
	def _load_file(self, url):
		self._loaded.append(url)
		# What a failing stat() produces: same cells as the placeholder.
		return f(url, [c('a')], is_loaded=True)
	def setUp(self):
		super().setUp()
		self._loaded = []
		self._model = Model(StubFileSystem({}), 'null://', [Column()])
		self._model._load_file = self._load_file

class InitStreamsFilesTest(ExecutorTestCase):

	"""
	#_init(...) used to drain iterdir(...) completely before committing a single
	row. On a slow file system - network:// enumerating shares - that left the
	pane empty for the whole enumeration.
	"""

	def test_slow_listing_shows_rows_early(self):
		self._patch('_INIT_BATCH_SECS', 0)
		self._init(['a', 'b', 'c'])
		self.assertEqual([0, 1, 2], self._rows_while_listing)
		self.assertEqual(3, self._model.rowCount())
	def test_fast_listing_commits_once(self):
		self._init(['a', 'b', 'c'])
		self.assertEqual([0, 0, 0], self._rows_while_listing)
		self.assertEqual(3, self._model.rowCount())
	def _patch(self, attribute, value):
		patcher = patch.object(model_module, attribute, value)
		patcher.start()
		self.addCleanup(patcher.stop)
	def _init(self, file_names):
		def iterdir(_):
			for file_name in file_names:
				self._rows_while_listing.append(self._model.rowCount())
				yield file_name
		self._fs.iterdir = iterdir
		# Bypass @transaction: it submits to a worker thread that these tests
		# never start.
		Model._init.__wrapped__(self._model, lambda: None)
	def setUp(self):
		super().setUp()
		self._rows_while_listing = []
		self._fs = StubFileSystem({})
		self._model = Model(self._fs, 'stub://', [NameColumn()])
		self._model._file_watcher = MagicMock(spec=FileWatcher)
		self._model._load_remaining_files = lambda *_, **__: None
		# The real one builds a QPixmap, which aborts without a QApplication:
		self._patch('_get_empty_icon', lambda *_: None)

class NameColumn(Column):
	def get_str(self, url):
		return basename(url)

def f(url, cells, is_loaded=False, is_dir=False):
	return File(url, None, is_dir, cells, is_loaded)

def c(str_, sort_value_asc=0, sort_value_desc=_NOT_LOADED):
	return Cell(str_, sort_value_asc, sort_value_desc)

class StubApp(QObject):
	aboutToQuit = pyqtSignal()