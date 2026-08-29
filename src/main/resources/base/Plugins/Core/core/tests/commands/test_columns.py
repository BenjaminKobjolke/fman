from core.commands.columns import _find_column_index
from unittest import TestCase

class FindColumnIndexTest(TestCase):
	_COLUMNS = ['core.Name', 'core.Size', 'core.Modified']
	def test_present(self):
		self.assertEqual(1, _find_column_index(self._COLUMNS, 'core.Size'))
	def test_absent(self):
		# The Windows drives view only has a DriveName column - Size/Modified
		# don't exist there, so toggling must not raise.
		self.assertIsNone(
			_find_column_index(['core.DriveName'], 'core.Size')
		)
