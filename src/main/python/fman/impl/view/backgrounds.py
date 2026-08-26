"""
Drawing the background images a theme places, and telling the widgets
above them to stop painting over them.

The Qt half of impl/background.py, which owns the rules and stays
importable without a QApplication. This half owns the pixmaps: loading
them, scaling them, and keeping both so that scrolling a pane does not
re-read and re-scale the same file on every repaint - the same reason
IconProvider caches. See docs/THEMES.md.
"""
from fman.impl.background import TILE, place
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

# The dynamic property that switches a widget's opaque background off in
# styles.qss. A Qt property selector rather than a local stylesheet:
# the Core plugin's pane font zoom replaces FileListView's local
# stylesheet wholesale, so anything written there is erased on the next
# zoom.
TRANSPARENT_PROPERTY = 'fman_background'

def set_transparent(widget, transparent):
	"""
	Turns TRANSPARENT_PROPERTY on or off on `widget` and re-polishes it.
	Qt only re-evaluates property selectors on unpolish/polish, so the
	stylesheet would otherwise keep the value the widget was created
	with. Does nothing when the flag is already right, because polishing
	restyles the widget and its children.
	"""
	if bool(widget.property(TRANSPARENT_PROPERTY)) == bool(transparent):
		return
	widget.setProperty(TRANSPARENT_PROPERTY, bool(transparent))
	widget.style().unpolish(widget)
	widget.style().polish(widget)

class BackgroundPainter:

	"""
	Draws Backgrounds into a rectangle. One instance is shared by every
	surface (see PAINTER below) so two panes showing the same image hold
	one pixmap between them rather than one each.
	"""

	def __init__(self):
		self._pixmaps = {}
		# Only the most recent scaled result per image is kept. Keying
		# by size as well would grow without bound while the user drags
		# the window edge, which is exactly when the cache matters most.
		self._scaled = {}

	def paint(self, painter, rect, backgrounds):
		"""
		Draws `backgrounds` into `rect` of `painter`'s device, in order,
		so a later entry covers an earlier one. Leaves the painter's
		opacity as it found it.
		"""
		for background in backgrounds:
			pixmap = self._pixmap(background.path)
			if pixmap.isNull():
				continue
			painter.setOpacity(background.opacity)
			if background.fit == TILE:
				painter.drawTiledPixmap(rect, pixmap)
			else:
				self._draw(painter, rect, background, pixmap)
		painter.setOpacity(1.0)

	def _draw(self, painter, rect, background, pixmap):
		x, y, width, height = place(
			pixmap.width(), pixmap.height(), rect.width(), rect.height(),
			background.fit, background.anchor
		)
		if width <= 0 or height <= 0:
			return
		painter.drawPixmap(
			rect.x() + x, rect.y() + y,
			self._scaled_pixmap(background.path, pixmap, width, height)
		)

	def _pixmap(self, path):
		# A file Qt cannot decode gives a null QPixmap, which paint()
		# skips - the same outcome as a theme asking for no image, and
		# the reason impl/background.py only checks that the file exists.
		try:
			return self._pixmaps[path]
		except KeyError:
			result = self._pixmaps[path] = QPixmap(path)
			return result

	def _scaled_pixmap(self, path, pixmap, width, height):
		if (width, height) == (pixmap.width(), pixmap.height()):
			return pixmap
		cached = self._scaled.get(path)
		if cached is not None and (cached.width(), cached.height()) == \
				(width, height):
			return cached
		# Qt.IgnoreAspectRatio: place() already decided both dimensions,
		# including the crop that "cover" means. Asking Qt to preserve
		# the ratio here would silently undo that.
		result = self._scaled[path] = pixmap.scaled(
			width, height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation
		)
		return result

# Shared by MainWindow and every FileListView. A module-level instance
# rather than one per widget: the panes of a theme with one wallpaper
# would otherwise hold one copy of it each.
PAINTER = BackgroundPainter()
