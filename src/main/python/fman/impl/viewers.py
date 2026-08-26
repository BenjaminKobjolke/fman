"""
The registry behind "View file": which fman.Viewer, if any, handles a given
url. Viewers are discovered the same way FileSystems and Columns are - a
plugin subclasses fman.Viewer and the plugin loader picks the class up (see
impl/plugins/plugin.py) - so unloading a plugin takes its viewers with it.

Registration order is plugin load order, which is not a useful priority: the
Core plugin loads first and its text viewer matches anything that sniffs as
text, so it would swallow every file type a later plugin wanted to claim.
Hence Viewer.priority, which is what actually decides between two viewers
that both match; order only breaks ties.
"""

class ViewerRegistry:
	def __init__(self):
		# (priority, sequence, viewer), kept sorted so find() is a plain scan.
		# `sequence` makes the sort stable across equal priorities without
		# comparing viewers, which have no ordering of their own.
		self._entries = []
		self._next_sequence = 0
	def register(self, viewer):
		self.unregister(viewer.name)
		self._entries.append((viewer.priority, self._next_sequence, viewer))
		self._next_sequence += 1
		self._entries.sort(key=lambda entry: (-entry[0], entry[1]))
	def unregister(self, name):
		# Silently ignores an unknown name: plugin unload replays inverse
		# actions, and a viewer that never made it into the registry must not
		# make unloading fail.
		self._entries = [e for e in self._entries if e[2].name != name]
	def find(self, url):
		"""
		The highest-priority Viewer whose matches(url) says yes, or None if no
		viewer handles this url.
		"""
		for _priority, _sequence, viewer in self._entries:
			try:
				if viewer.matches(url):
					return viewer
			except Exception:
				# Plugin viewers reach here already wrapped (ViewerWrapper,
				# impl/plugins/plugin.py), but the registry must not depend on
				# that: one broken viewer cannot be allowed to break View file
				# for every other one.
				continue
		return None
	def for_category(self, name):
		"""
		The Viewer registered under `name`, or None. Used where a category is
		stored rather than a url - the per-viewer "advance only for same type"
		settings key, for instance.
		"""
		for _priority, _sequence, viewer in self._entries:
			if viewer.name == name:
				return viewer
		return None
