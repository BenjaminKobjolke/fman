from fman import Viewer
from fman.impl.viewers import ViewerRegistry
from unittest import TestCase

class _StubViewer(Viewer):
	def __init__(self, name, priority=0, matching=(), raises=False):
		self.name = name
		self.priority = priority
		self.shown = []
		self._matching = matching
		self._raises = raises
	def matches(self, url):
		if self._raises:
			raise ValueError('boom')
		return url in self._matching
	def show(self, pane, url, focus_view=True):
		self.shown.append((pane, url, focus_view))

class ViewerRegistryTest(TestCase):

	"""
	The lookup behind "View file": which Viewer, if any, handles a url.
	Registration order is plugin load order, so priority - not order - is what
	decides between two viewers that both match.
	"""

	def setUp(self):
		self.registry = ViewerRegistry()

	def test_no_viewers_registered_matches_nothing(self):
		self.assertIsNone(self.registry.find('file://a.txt'))

	def test_finds_the_viewer_that_matches(self):
		image = _StubViewer('image', matching=('file://a.png',))
		self.registry.register(image)
		self.assertIs(image, self.registry.find('file://a.png'))
		self.assertIsNone(self.registry.find('file://a.txt'))

	def test_higher_priority_wins_regardless_of_registration_order(self):
		# The Core text viewer is a catch-all sniffer registered before any
		# plugin. Without priority it would swallow every plugin's file type.
		text = _StubViewer('text', priority=-100, matching=('file://a.md',))
		markdown = _StubViewer('markdown', matching=('file://a.md',))
		self.registry.register(text)
		self.registry.register(markdown)
		self.assertIs(markdown, self.registry.find('file://a.md'))

	def test_equal_priority_falls_back_to_registration_order(self):
		first = _StubViewer('first', matching=('file://a.x',))
		second = _StubViewer('second', matching=('file://a.x',))
		self.registry.register(first)
		self.registry.register(second)
		self.assertIs(first, self.registry.find('file://a.x'))

	def test_unregister_removes_the_viewer(self):
		image = _StubViewer('image', matching=('file://a.png',))
		self.registry.register(image)
		self.registry.unregister('image')
		self.assertIsNone(self.registry.find('file://a.png'))

	def test_unregister_of_an_unknown_name_is_harmless(self):
		# Plugin unload replays inverse actions; a viewer that failed to
		# register must not make unloading blow up.
		self.registry.unregister('never-registered')

	def test_a_viewer_that_raises_is_skipped_not_fatal(self):
		# Belt-and-braces: ViewerWrapper already swallows this for plugin
		# viewers, but the registry must not depend on being wrapped.
		self.registry.register(_StubViewer('broken', raises=True))
		fallback = _StubViewer('text', priority=-100, matching=('file://a.txt',))
		self.registry.register(fallback)
		self.assertIs(fallback, self.registry.find('file://a.txt'))

	def test_for_category_looks_a_viewer_up_by_name(self):
		image = _StubViewer('image')
		self.registry.register(image)
		self.assertIs(image, self.registry.for_category('image'))
		self.assertIsNone(self.registry.for_category('video'))

class ViewerBaseClassTest(TestCase):

	def test_matches_nothing_by_default(self):
		self.assertFalse(Viewer().matches('file://a.txt'))

	def test_show_must_be_implemented(self):
		with self.assertRaises(NotImplementedError):
			Viewer().show(None, 'file://a.txt')
