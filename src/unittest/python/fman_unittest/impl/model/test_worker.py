from fman.impl.model.worker import Worker, WorkItem
from threading import Event
from unittest import TestCase

class WorkerTest(TestCase):
	def test_submit_forwards_keyword_arguments(self):
		received = {}
		done = Event()
		def fn(*args, **kwargs):
			received['args'] = args
			received['kwargs'] = kwargs
			done.set()
		worker = Worker()
		worker.start()
		self.addCleanup(worker.shutdown)
		worker.submit(1, fn, 'a', key='value')
		self.assertTrue(done.wait(1))
		self.assertEqual(('a',), received['args'])
		self.assertEqual({'key': 'value'}, received['kwargs'])
	def test_shutdown_from_worker_thread(self):
		# Model#_shutdown_async() runs *on* the worker. A thread can't join
		# itself, so this used to raise RuntimeError.
		errors = []
		def shutdown():
			try:
				worker.shutdown()
			except RuntimeError as e:
				errors.append(e)
		worker = Worker()
		worker.start()
		worker.submit(1, shutdown)
		worker._thread.join(2)
		self.assertFalse(worker._thread.is_alive())
		self.assertEqual([], errors)

class WorkItemTest(TestCase):
	def test_equal(self):
		self.assertEqual(
			WorkItem(1, self._fn, 'a', key='value'),
			WorkItem(1, self._fn, 'a', key='value')
		)
	def test_not_equal_args(self):
		self.assertNotEqual(
			WorkItem(1, self._fn, 'a'), WorkItem(1, self._fn, 'b')
		)
	def test_not_equal_priority(self):
		self.assertNotEqual(WorkItem(1, self._fn), WorkItem(2, self._fn))
	def test_not_equal_other_type(self):
		self.assertNotEqual(WorkItem(1, self._fn), 1)
	@staticmethod
	def _fn(*_, **__):
		pass
