"""
Runs the tasks a FileTreeOperation gathers on one or more worker threads. Slow
per-file transports (FTP) gain from several. The progress dialog polls
snapshot() and calls add() / remove() while the workers run.
"""
from dataclasses import dataclass, replace
from fman.impl.task import ChildProgressDialog
from threading import Lock, Thread

# Ends the queue of tasks. It stays in the queue so every worker sees it.
DONE = object()

_MAX_WORKERS = 10

@dataclass
class WorkerState:
	id: int
	title: str = ''
	progress: int = 0
	size: int = 0
	retiring: bool = False

class TransferWorkers:
	def __init__(self, count, queue, run_task, should_stop=lambda: False):
		"""
		run_task(worker, task, is_last) runs one task and returns False to
		stop all workers. should_stop() is checked before each task.
		"""
		self._count = count
		self._queue = queue
		self._run_task = run_task
		self._should_stop = should_stop
		self._lock = Lock()
		self._workers = []
		self._threads = []
		self._next_id = 1
		self._aborted = False
		self._finished = False
		self._error = None
	def start(self):
		if self._count == 1:
			# Runs to the end right here: no worker view is shown, so nothing
			# can add() a second worker.
			with self._lock:
				worker = self._new_worker()
			self._work(worker)
		else:
			for _ in range(self._count):
				self.add()
	def join(self):
		while True:
			with self._lock:
				threads = [t for t in self._threads if t.is_alive()]
				if not threads:
					self._finished = True
					break
			# Workers added meanwhile are picked up by the next round.
			for thread in threads:
				thread.join()
		if self._error is not None:
			raise self._error
	def can_add(self):
		with self._lock:
			return self._can_add()
	def add(self):
		with self._lock:
			if not self._can_add():
				return
			worker = self._new_worker()
			thread = Thread(target=self._work, args=(worker,), daemon=True)
			self._threads.append(thread)
			thread.start()
	def can_remove(self):
		with self._lock:
			return self._can_remove()
	def remove(self):
		# The worker finishes its active task first. One blocked waiting for
		# a task runs the one it gets, then stops.
		with self._lock:
			if self._can_remove():
				self._active_workers()[-1].retiring = True
	def snapshot(self):
		with self._lock:
			return [replace(worker) for worker in self._workers]
	def _can_add(self):
		return not (self._finished or self._aborted) and \
			len(self._workers) < _MAX_WORKERS
	def _can_remove(self):
		# At least one worker always stays.
		return len(self._active_workers()) > 1
	def _active_workers(self):
		return [w for w in self._workers if not w.retiring]
	def _new_worker(self):
		result = WorkerState(self._next_id)
		self._next_id += 1
		self._workers.append(result)
		return result
	def _work(self, worker):
		try:
			while not (self._aborted or worker.retiring):
				task = self._queue.get()
				if task is DONE:
					self._queue.put(DONE)
					break
				is_last = self._next_is_done()
				if self._aborted or self._should_stop():
					break
				if not self._run_task(worker, task, is_last):
					self._aborted = True
		except BaseException as e:
			self._aborted = True
			with self._lock:
				if self._error is None:
					self._error = e
		finally:
			with self._lock:
				self._workers.remove(worker)
	def _next_is_done(self):
		# Waits for the next task like a look-ahead, but does not take it: it
		# may become another worker's. Queue has no public peek.
		queue = self._queue
		with queue.not_empty:
			while not queue.queue:
				queue.not_empty.wait()
			# put(...) wakes one waiter. Not taking the item, pass the wakeup
			# on, or a second peeking worker sleeps forever.
			queue.not_empty.notify()
			return queue.queue[0] is DONE

class WorkerProgress(ChildProgressDialog):
	"""
	The dialog of a task a worker runs. ChildProgressDialog sets the parent's
	progress absolutely, so tasks running in parallel would overwrite each
	other. This one adds the change instead.
	"""
	def __init__(self, parent, lock, worker, task, forward_text):
		super().__init__(parent)
		self._lock = lock
		self._worker = worker
		self._forward_text = forward_text
		self._done = 0
		worker.size = task.get_size()
		worker.progress = 0
		self.set_text(task.get_title())
	def set_text(self, status):
		self._worker.title = status
		if self._forward_text:
			super().set_text(status)
	def set_progress(self, progress):
		with self._lock:
			self._parent.set_progress(
				self._parent.get_progress() + progress - self._done
			)
			self._done = progress
		self._worker.progress = progress
	def get_progress(self):
		return self._done
