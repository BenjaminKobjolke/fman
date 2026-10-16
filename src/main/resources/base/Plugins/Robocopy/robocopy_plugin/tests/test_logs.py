from pathlib import Path
import tempfile
import unittest

from robocopy_plugin.logs import FINISHED, TransferLog, choose_path


class TransferLogTest(unittest.TestCase):
	def test_log_is_unicode_exclusive_and_only_completed_logs_are_pruned(self):
		with tempfile.TemporaryDirectory() as temporary:
			path = Path(choose_path(temporary))
			log = TransferLog(path, 'Copy with robocopy')
			self.assertTrue(path.read_bytes().startswith(b'\xff\xfe'))
			log.append('file.txt')
			with self.assertRaises(FileExistsError):
				TransferLog(path, 'second')
			incomplete = path.with_name('20000101T000000000000Z-' + 'a' * 32 + '.txt')
			incomplete.write_bytes(b'not a completed log')
			log.finish('Copied files')
			log.prune(1)
			self.assertTrue(path.exists())
			self.assertTrue(incomplete.exists())
			self.assertTrue(path.read_bytes().endswith(FINISHED))

	def test_validate_rejects_truncated_or_replaced_log(self):
		with tempfile.TemporaryDirectory() as temporary:
			path = Path(choose_path(temporary))
			log = TransferLog(path, 'Copy')
			with path.open('ab') as output:
				output.write(b'\x00')
			with self.assertRaisesRegex(OSError, 'incomplete'):
				log.validate()
			path.unlink()
			path.write_bytes(b'\xff\xfe\x00\x00')
			with self.assertRaisesRegex(OSError, 'changed'):
				log.validate()

	def test_path_is_inside_local_robocopy_log_directory(self):
		with tempfile.TemporaryDirectory() as temporary:
			path = Path(choose_path(temporary))
			self.assertEqual(
				Path(temporary) / 'Local' / 'Robocopy' / 'Logs', path.parent
			)
