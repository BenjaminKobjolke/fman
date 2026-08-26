from core.fs.zip import remove_7zip_temp_archive
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

class Remove7ZipTempArchiveTest(TestCase):
	def test_removes_temp_of_updated_archive(self):
		self._make_temp_archive()
		remove_7zip_temp_archive(['a', self._archive, 'file.txt'])
		self.assertFalse(self._temp_archive.exists())
	def test_ignores_switches_before_the_command(self):
		self._make_temp_archive()
		remove_7zip_temp_archive(['-sccWIN', '-bsp1', 'rn', self._archive, 'a', 'b'])
		self.assertFalse(self._temp_archive.exists())
	def test_resolves_relative_archive_against_cwd(self):
		self._make_temp_archive()
		remove_7zip_temp_archive(['a', 'a.zip', 'file.txt'], cwd=self._dir.name)
		self.assertFalse(self._temp_archive.exists())
	def test_keeps_temp_of_read_only_commands(self):
		self._make_temp_archive()
		remove_7zip_temp_archive(['x', self._archive, '-o' + self._dir.name])
		self.assertTrue(self._temp_archive.exists())
	def test_missing_temp_is_not_an_error(self):
		self._make_temp_archive()
		self._temp_archive.unlink()
		remove_7zip_temp_archive(['a', self._archive, 'file.txt'])
	def test_too_few_operands_is_not_an_error(self):
		remove_7zip_temp_archive(['a'])
	def _make_temp_archive(self):
		self._dir = TemporaryDirectory()
		self.addCleanup(self._dir.cleanup)
		self._archive = str(Path(self._dir.name, 'a.zip'))
		self._temp_archive = Path(self._archive + '.tmp')
		self._temp_archive.write_bytes(b'incomplete')
