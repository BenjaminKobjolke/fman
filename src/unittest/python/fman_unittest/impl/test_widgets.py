from fman.impl.widgets import LOADING_MESSAGE, LOADING_MESSAGE_NETWORK, \
	format_loading_message
from unittest import TestCase

class FormatLoadingMessageTest(TestCase):

	"""
	The elapsed seconds are what tell the user the app is still working. A
	message that does not change reads as a freeze.
	"""

	def test_shows_whole_elapsed_seconds(self):
		self.assertIn('(12 s)', format_loading_message(LOADING_MESSAGE, 12.7))
	def test_starts_with_the_title(self):
		text = format_loading_message(LOADING_MESSAGE_NETWORK, 3.0)
		self.assertTrue(text.startswith(LOADING_MESSAGE_NETWORK.title), text)
	def test_detail_is_below_the_title(self):
		title, blank, first_detail_line = \
			format_loading_message(LOADING_MESSAGE, 1.0).split('\n')[:3]
		self.assertEqual(LOADING_MESSAGE.title, title)
		self.assertEqual('', blank)
		self.assertTrue(first_detail_line)
