"""Shared file-system test doubles used by fman's unit and Core tests."""

from fman.fs import FileSystem, cached
from fman.impl.util import filenotfounderror
from fman.impl.util.path import normalize


class CachedStubFileSystem(FileSystem):
	@cached
	def is_dir(self, existing_path):
		path_resolved = normalize(existing_path)
		try:
			item = self._items[path_resolved]
		except KeyError:
			raise filenotfounderror(existing_path)
		return item.get('is_dir', False)
	@cached
	def size_bytes(self, path):
		return self._items[normalize(path)].get('size', 1)
	@cached
	def modified_datetime(self, path):
		return self._items[normalize(path)].get('mtime', 1473339041.0)
	def touch(self, path):
		file_existed = self.exists(path)
		self._items[normalize(path)] = {}
		if not file_existed:
			self.notify_file_added(path)
