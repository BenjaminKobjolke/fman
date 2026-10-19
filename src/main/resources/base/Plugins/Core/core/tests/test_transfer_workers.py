from core.transfer_workers import TransferWorkers, DONE
from queue import Queue
from threading import Barrier, Event, get_ident
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
	def _start(self, count, tasks, run_task):
		result = TransferWorkers(count, self._queue_of(tasks), run_task)
		result.start()
		return result
	def _queue_of(self, tasks):
		result = Queue()
		for task in tasks + [DONE]:
			result.put(task)
		return result
