from fman.impl.model.icon_tint import tint_image
from PyQt5.QtGui import QColor, QImage
from unittest import TestCase

_GREEN = '#00ff41'

def _image(*pixels):
	"""
	A 1-row ARGB32 image of `pixels`, each an (r, g, b, a) tuple. QImage
	needs no QApplication, which is the whole reason the tint math lives
	apart from icon_provider's QIcon and QPixmap.
	"""
	result = QImage(len(pixels), 1, QImage.Format_ARGB32)
	for x, (r, g, b, a) in enumerate(pixels):
		result.setPixelColor(x, 0, QColor(r, g, b, a))
	return result

def _pixel(image, x=0):
	return image.convertToFormat(QImage.Format_ARGB32).pixelColor(x, 0)

class TintImageTest(TestCase):

	"""
	Recoloring an icon: the tint's hue everywhere, each pixel's own
	brightness and alpha kept.
	"""

	def test_transparent_pixel_stays_transparent(self):
		# The icons are mostly transparent, so getting this wrong would draw
		# a solid colored square per file rather than an icon.
		result = tint_image(_image((255, 255, 255, 0)), _GREEN)
		self.assertEqual(0, _pixel(result).alpha())
	def test_white_pixel_takes_the_color(self):
		result = tint_image(_image((255, 255, 255, 255)), _GREEN)
		self.assertEqual(QColor(_GREEN).getRgb(), _pixel(result).getRgb())
	def test_black_pixel_stays_black(self):
		# Multiply by zero brightness. This is what keeps an icon's outlines
		# and shadows rather than flooding them with the tint.
		result = tint_image(_image((0, 0, 0, 255)), _GREEN)
		self.assertEqual((0, 0, 0), _pixel(result).getRgb()[:3])
	def test_opacity_is_kept(self):
		result = tint_image(_image((255, 255, 255, 128)), _GREEN)
		self.assertEqual(128, _pixel(result).alpha())
	def test_a_saturated_pixel_of_another_hue_takes_the_tint(self):
		# The regression the desaturating pass exists for: multiplying a blue
		# icon by a green tint directly cancels both channels to near-black.
		# Material's icons are saturated, so this is the common case, not an
		# edge case.
		result = tint_image(_image((0, 0, 255, 255)), _GREEN)
		self.assertEqual(QColor(_GREEN).hue(), _pixel(result).hue())
		self.assertGreater(_pixel(result).value(), 0)
	def test_brightness_is_kept_relative(self):
		# A brighter source pixel must stay the brighter of the two, or the
		# icon's shading is gone even though its color is right.
		result = tint_image(
			_image((64, 64, 64, 255), (192, 192, 192, 255)), _GREEN
		)
		self.assertLess(_pixel(result, 0).value(), _pixel(result, 1).value())
	def test_the_source_image_is_not_modified(self):
		# tint_image paints on a converted copy. QImage is implicitly shared,
		# so painting on the original would reach the caller's icon too.
		image = _image((255, 255, 255, 255))
		tint_image(image, _GREEN)
		self.assertEqual((255, 255, 255), _pixel(image).getRgb()[:3])
