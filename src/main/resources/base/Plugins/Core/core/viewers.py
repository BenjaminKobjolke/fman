"""
The Core plugin's three built-in viewers, expressed as fman.Viewer subclasses
so they go through the same registry a plugin's viewer does (see
docs/viewers/PLUGIN_VIEWERS.md). Each is a thin declaration of "which files do
I handle" plus a call into the show_*_viewer function that already existed -
the viewer widgets themselves are untouched, in core/textviewer.py,
core/imageviewer.py and core/videoviewer.py.

Collected in one module rather than one per viewer file because the plugin
loader only discovers classes reachable from core/__init__.py's namespace, so
each would otherwise need its own re-export.
"""
from core.imageviewer import is_image, show_image_viewer
from core.textviewer import show_text_viewer
from core.textviewer_io import is_text_file
from core.videoviewer import is_video, show_video_viewer
from fman import find_viewer, viewer_for_category, Viewer
from fman.fs import is_dir
from fman.url import as_human_readable, splitscheme

class ImageViewer(Viewer):
	name = 'image'
	def matches(self, url):
		return is_image(url)
	def show(self, pane, url, focus_view=True):
		show_image_viewer(pane, url, focus_view=focus_view)

class VideoViewer(Viewer):
	name = 'video'
	def matches(self, url):
		return is_video(url)
	def show(self, pane, url, focus_view=True):
		show_video_viewer(pane, url, focus_view=focus_view)

class TextViewer(Viewer):

	# The catch-all: is_text_file sniffs rather than matching an extension, so
	# it says yes to anything that is not an image, a video or a binary. Sits
	# below the default 0 so a plugin claiming, say, .md gets first refusal.
	priority = -100

	name = 'text'
	def matches(self, url):
		return is_text_file(as_human_readable(url))
	def show(self, pane, url, focus_view=True):
		show_text_viewer(pane, url, focus_view=focus_view)

def viewer_for(url):
	"""
	find_viewer(url), but only for local files - the guard the three viewers
	above would otherwise each have to repeat, and which TextViewer in
	particular needs: is_text_file would try to read a directory.

	Returns None for a directory or a non-local url, matching what "View file"
	has always done (it alerts on both rather than picking a viewer).
	"""
	if splitscheme(url)[0] != 'file://':
		return None
	if is_dir(url):
		return None
	return find_viewer(url)
