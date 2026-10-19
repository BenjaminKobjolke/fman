from core.transfer_workers import TransferWorkers, DONE
from queue import Queue
from threading import Barrier, Event, get_ident
from time import sleep
from unittest import TestCase

class TransferWorkersTest(TestCase):

	_TIMEOUT_SECS = 5

	def test_workers_run_tasks_at_the_same_time(self):
		# Passes only if all three tasks run at once:
		barrier = Barrier(3, timeout=self._TIMEOUT_SECS)
		ran = []
		def run_task(worker, task, is_last):
			barrier.wait()
			ran.append(task)
			return True
		self._start(3, ['a', 'b', 'c'], run_task).join()
		self.assertEqual({'a', 'b', 'c'}, set(ran))
	def test_single_worker_runs_on_calling_thread(self):
		threads = []
		def run_task(worker, task, is_last):
			threads.append(get_ident())
			return True
		self._start(1, ['a'], run_task).join()
		self.assertEqual([get_ident()], threads)
	def test_is_last_marks_final_task(self):
		flags = []
		def run_task(worker, task, is_last):
			flags.append(is_last)
			return True
		self._start(1, ['a', 'b'], run_task).join()
		self.assertEqual([False, True], flags)
	def test_abort_skips_remaining_tasks(self):
		ran = []
		def run_task(worker, task, is_last):
			ran.append(task)
			return False
		self._start(1, ['a', 'b'], run_task).join()
		self.assertEqual(['a'], ran)
	def test_should_stop_skips_remaining_tasks(self):
		ran = []
		def run_task(worker, task, is_last):
			ran.append(task)
			return True
		workers = TransferWorkers(
			1, self._queue_of(['a', 'b']), run_task, should_stop=lambda: ran
		)
		workers.start()
		workers.join()
		self.assertEqual(['a'], ran)
	def test_join_reraises_worker_error(self):
		def run_task(worker, task, is_last):
			raise ValueError(task)
		workers = self._start(2, ['a', 'b'], run_task)
		with self.assertRaises(ValueError):
			workers.join()
	def test_remove_lets_active_task_finish(self):
		both_started = Barrier(3, timeout=self._TIMEOUT_SECS)
		release = Event()
		ran_by = {}
		def run_task(worker, task, is_last):
			if task in ('a', 'b'):
				both_started.wait()
				release.wait(self._TIMEOUT_SECS)
			ran_by[task] = worker.id
			return True
		workers = self._start(2, ['a', 'b', 'c', 'd'], run_task)
		both_started.wait()
		workers.remove()
		self.assertFalse(
			workers.can_remove(), 'The last worker must not be removable.'
		)
		retiring = [w.id for w in workers.snapshot() if w.retiring]
		self.assertEqual(1, len(retiring))
		release.set()
		workers.join()
		self.assertEqual({'a', 'b', 'c', 'd'}, set(ran_by))
		tasks_of_retired = [t for t, w in ran_by.items() if w == retiring[0]]
		self.assertEqual(
			1, len(tasks_of_retired), 'Retired after its active task only.'
		)
	def test_add_starts_another_worker(self):
		barrier = Barrier(3, timeout=self._TIMEOUT_SECS)
		def run_task(worker, task, is_last):
			barrier.wait()
			return True
		workers = self._start(2, ['a', 'b', 'c'], run_task)
		workers.add()
		workers.join()
	def test_worker_ids_are_not_reused(self):
		release = Event()
		def run_task(worker, task, is_last):
			release.wait(self._TIMEOUT_SECS)
			return True
		workers = self._start(2, ['a', 'b'], run_task)
		workers.remove()
		workers.add()
		ids = [w.id for w in workers.snapshot()]
		release.set()
		workers.join()
		self.assertEqual(len(ids), len(set(ids)))
		self.assertIn(3, ids)
	def test_barrier_task_waits_for_earlier_tasks(self):
		a_started, release_a = Event(), Event()
		events = []
		def run_task(worker, task, is_last):
			events.append(('start', task))
			if task == 'a':
				a_started.set()
				release_a.wait(self._TIMEOUT_SECS)
			events.append(('end', task))
			return True
		barrier = _flagged('b', waits_for_earlier_tasks=True)
		workers = self._start(2, ['a', barrier], run_task)
		a_started.wait(self._TIMEOUT_SECS)
		# Gives a broken barrier the time to start 'b' too early:
		sleep(.2)
		release_a.set()
		workers.join()
		self.assertLess(events.index(('end', 'a')), events.index(('start', 'b')))
	def test_blocking_task_holds_back_later_tasks_only(self):
		a_started, release_a = Event(), Event()
		mkdir_started, release_mkdir = Event(), Event()
		events = []
		def run_task(worker, task, is_last):
			events.append(('start', task))
			if task == 'a':
				a_started.set()
				release_a.wait(self._TIMEOUT_SECS)
			elif task == 'mkdir':
				mkdir_started.set()
				release_mkdir.wait(self._TIMEOUT_SECS)
			events.append(('end', task))
			return True
		mkdir = _flagged('mkdir', blocks_later_tasks=True)
		workers = self._start(3, ['a', mkdir, 'c'], run_task)
		a_started.wait(self._TIMEOUT_SECS)
		self.assertTrue(
			mkdir_started.wait(self._TIMEOUT_SECS),
			'A blocking task must not wait for the tasks before it.'
		)
		# Gives a broken implementation the time to start 'c' too early:
		sleep(.2)
		release_mkdir.set()
		release_a.set()
		workers.join()
		self.assertLess(
			events.index(('end', 'mkdir')), events.index(('start', 'c'))
		)
	def test_counts_before_start_and_after_join(self):
		workers = TransferWorkers(
			2, self._queue_of(['a', 'b', 'c']), lambda *_: True
		)
		self.assertEqual((0, 3), workers.counts())
		workers.start()
		workers.join()
		self.assertEqual((3, 3), workers.counts())
	def test_count_total_grows_with_the_queue(self):
		a_started, release_a = Event(), Event()
		def run_task(worker, task, is_last):
			a_started.set()
			release_a.wait(self._TIMEOUT_SECS)
			return True
		queue = Queue()
		queue.put('a')
		workers = TransferWorkers(2, queue, run_task)
		workers.start()
		a_started.wait(self._TIMEOUT_SECS)
		self.assertEqual((0, 1), workers.counts())
		queue.put('b')
		queue.put(DONE)
		self.assertEqual(2, workers.counts()[1])
		release_a.set()
		workers.join()
		self.assertEqual((2, 2), workers.counts())
	def _start(self, count, tasks, run_task):
		result = TransferWorkers(count, self._queue_of(tasks), run_task)
		result.start()
		return result
	def _queue_of(self, tasks):
		result = Queue()
		for task in tasks + [DONE]:
			result.put(task)
		return result

class _Flagged(str):
	pass

def _flagged(name, **flags):
	# A str, so run_task can compare it to plain names, with Task's flags.
	result = _Flagged(name)
	result.__dict__.update(flags)
	return result
