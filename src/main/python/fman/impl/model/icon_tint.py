"""
Recoloring an icon set's icons to the color a theme asks for.

Split from icon_provider.py so the pixel work can be tested: everything
here is QImage, which needs no QApplication, while the QPixmap and QIcon
the file list actually draws do. That is the same seam _load_icon already
was - see icon_provider._load_icon and docs/ICONS.md.

The recolor keeps each icon's own light and dark areas instead of flooding
it with one flat color, so a Material icon still reads as itself under a
theme's tint rather than becoming a silhouette.
"""
from PyQt5.QtGui import QColor, QImage, QPainter

# What a tinted icon is rasterized at. An untinted QIcon(path) lets Qt's SVG
# engine redraw at whatever size the view asks for; a tint has to pick one
# size and let Qt scale from there. 128 leaves headroom over MAX_ICON_SIZE
# (64) for HiDPI screens, which ask for twice the logical size.
TINT_RENDER_SIZE = 128

def tint_image(image, color):
	"""
	`image` recolored to `color`, keeping each pixel's own brightness and its
	own alpha: a transparent pixel stays transparent, a dark one stays dark,
	a bright one takes the color fully.

	Three QPainter passes rather than a Python loop over the pixels. A single
	directory listing can show dozens of distinct icons, and at
	TINT_RENDER_SIZE each one is 16k pixels - a per-pixel round trip through
	Python would be paid on every one of them.
	"""
	# Convert away from premultiplied alpha *before* going to grayscale:
	# Grayscale8 reads the raw RGB channels, and in a premultiplied image a
	# half-transparent bright pixel is stored dark. Skipping this hop darkens
	# every antialiased edge.
	gray = image.convertToFormat(QImage.Format_ARGB32) \
		.convertToFormat(QImage.Format_Grayscale8) \
		.convertToFormat(QImage.Format_ARGB32_Premultiplied)
	painter = QPainter(gray)
	try:
		# Multiply against a gray image is what preserves the shading: the
		# result is the color scaled by each pixel's brightness. Desaturating
		# first is what makes it a recolor rather than a darkening - multiply
		# a blue icon by green directly and both channels cancel to mud.
		painter.setCompositionMode(QPainter.CompositionMode_Multiply)
		painter.fillRect(gray.rect(), QColor(color))
		# Grayscale8 has no alpha channel, so the conversion above made the
		# whole image opaque. Put the original's coverage back.
		painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
		painter.drawImage(0, 0, image)
	finally:
		# An unfinished QPainter on a QImage warns at garbage-collection time
		# and leaves the image unusable, so end it even if a pass raises.
		painter.end()
	return gray
