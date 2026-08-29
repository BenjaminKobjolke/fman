from core.font_size import clamp_font_size, MAX_FONT_SIZE, MIN_FONT_SIZE
from unittest import TestCase

class ClampFontSizeTest(TestCase):
	def test_steps_up(self):
		self.assertEqual(10, clamp_font_size(9, +1))
	def test_steps_down(self):
		self.assertEqual(8, clamp_font_size(9, -1))
	def test_clamps_at_minimum(self):
		self.assertEqual(
			MIN_FONT_SIZE, clamp_font_size(MIN_FONT_SIZE, -1)
		)
	def test_clamps_at_maximum(self):
		self.assertEqual(
			MAX_FONT_SIZE, clamp_font_size(MAX_FONT_SIZE, +1)
		)
