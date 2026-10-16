from fman_test_support import CachedStubFileSystem
from fman.impl.util.path import normalize
from fman.url import splitscheme, basename, dirname
from io import UnsupportedOperation

class StubFileSystem(CachedStubFileSystem):

	scheme = 'stub://'

	def __init__(self, items, default_columns=('core.Name',)):
		super().__init__()
		self._items = items
		self._default_columns = default_columns
	def get_default_columns(self, path):
		return self._default_columns
	def exists(self, path):
		return normalize(path) in self._items
	def iterdir(self, path):
		try:
			items = self._items[normalize(path)]
		except KeyError:
			raise FileNotFoundError(path) from None
		return list(items.get('files', []))
	def mkdir(self, path):
		if self.exists(path):
			raise FileExistsError(path)
		self._items[normalize(path)] = {'is_dir': True}
		self.notify_file_added(path)
	def move(self, src_url, dst_url):
		src_scheme, src_path = splitscheme(src_url)
		dst_scheme, dst_path = splitscheme(dst_url)
		if src_scheme != self.scheme or dst_scheme != self.scheme:
			raise UnsupportedOperation()
		self._items[normalize(dst_path)] = self._items.pop(normalize(src_path))
		self.notify_file_removed(src_path)
		self.notify_file_added(dst_path)
	def delete(self, path):
		path = normalize(path)
		new_items = {
			other_path: value for other_path, value in self._items.items()
			if other_path != path and not other_path.startswith(path)
		}
		self._items.clear()
		self._items.update(new_items)
		url = self.scheme + path
		parent, file_ = splitscheme(dirname(url))[1], basename(url)
		self._items[parent]['files'].remove(file_)
		self.notify_file_removed(path)
