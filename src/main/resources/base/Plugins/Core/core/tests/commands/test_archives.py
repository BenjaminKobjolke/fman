from core.commands.archives import _get_handler_for_archive
from unittest import TestCase
from unittest.mock import patch

class GetHandlerForArchiveTest(TestCase):

	"""
	The suffix -> scheme lookup behind "Enter opens a .zip like a folder".
	Handlers are tried longest suffix first, so '.tar.gz' cannot be stolen by
	a plugin that registered plain '.gz'.
	"""

	_HANDLERS = {
		'.zip': 'zip://',
		'.gz': 'gz://',
		'.tar.gz': 'tar.gz://',
	}

	def test_matches_a_registered_suffix(self):
		self.assertEqual('zip://', self._handler('archive.zip'))
	def test_longest_suffix_wins(self):
		self.assertEqual('tar.gz://', self._handler('archive.tar.gz'))
	def test_is_case_insensitive(self):
		self.assertEqual('zip://', self._handler('ARCHIVE.ZIP'))
	def test_unknown_suffix_has_no_handler(self):
		self.assertIsNone(self._handler('notes.txt'))
	def test_no_handlers_configured(self):
		self.assertIsNone(self._handler('archive.zip', handlers={}))
	def _handler(self, file_name, handlers=None):
		if handlers is None:
			handlers = self._HANDLERS
		with patch(
			'core.commands.archives.load_json',
			return_value={'archive_handlers': handlers}
		):
			return _get_handler_for_archive(file_name)
