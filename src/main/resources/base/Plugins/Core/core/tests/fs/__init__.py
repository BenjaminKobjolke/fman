from fman_test_support import CachedStubFileSystem
from fman.impl.util.path import normalize

class StubFileSystem(CachedStubFileSystem):

	scheme = 'stub://'

	def __init__(self, items):
		super().__init__()
		self._items = items
	def exists(self, path):
		return normalize(path) in self._items
