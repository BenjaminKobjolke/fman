from core.textviewer import _caret_fix_css
from unittest import TestCase

class CaretFixCssTest(TestCase):
	def test_embeds_given_background_and_foreground(self):
		css = _caret_fix_css('#2b2b2b', '#ffffff')
		self.assertIn('background-color: #2b2b2b', css)
		self.assertIn('color: #ffffff', css)

	def test_targets_only_qplaintextedit(self):
		# Must stay a type-selector rule (not '*') so it overrides the
		# app-wide wildcard font-size rule without leaking onto other widgets.
		css = _caret_fix_css('#000000', '#111111')
		self.assertTrue(css.startswith('QPlainTextEdit {'))

	def test_omits_font_size_when_not_given(self):
		self.assertNotIn('font-size', _caret_fix_css('#000000', '#111111'))

	def test_embeds_font_size_when_given(self):
		css = _caret_fix_css('#000000', '#111111', font_size=14)
		self.assertIn('font-size: 14pt', css)
