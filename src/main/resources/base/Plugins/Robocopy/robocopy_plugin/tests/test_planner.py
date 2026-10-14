import os
import importlib
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from robocopy_plugin.jobs import Source, build_jobs, command_units, exit_description
from robocopy_plugin.paths import absolute_path, contains, from_url, related
from robocopy_plugin.settings import Settings


def as_url(path: Path) -> str:
	return 'file://' + str(path).replace('\\', '/')


def directory_names(_path: str, _check: object):
	yield 'folder', ''


def file_names(_path: str, _check: object):
	yield 'file.txt', ''


class PlannerTest(unittest.TestCase):
	def test_windows_path_validation_and_relationships(self):
		self.assertEqual('C:\\folder', absolute_path('C:/folder'))
		self.assertEqual('C:\\folder', from_url('file://C:/folder'))
		self.assertTrue(contains('C:\\folder', 'c:\\folder\\child'))
		self.assertFalse(contains('C:\\folder', 'C:\\folder-two'))
		self.assertTrue(related('C:\\folder', 'C:\\folder\\child'))
		for path in ('relative', 'C:relative', 'file://C:/folder', 'C:\\file:stream',
				'\\\\?\\C:\\folder', 'C:\\bad. '):
			with self.subTest(path=path), self.assertRaises(ValueError):
				absolute_path(path)

	def test_files_are_batched_to_the_quoted_utf16_command_limit(self):
		entries = tuple(Source('C:\\source\\' + name, name, False, (1, index, 0))
			for index, name in enumerate('file %d 😀.txt' % index for index in range(40)))
		settings = Settings.load({})
		jobs = build_jobs('C:\\source', 'C:\\destination', entries,
			'C:\\Windows\\robocopy.exe', settings, limit=300)
		self.assertGreater(len(jobs), 1)
		self.assertEqual(tuple(entry.name for entry in entries),
			tuple(name for job in jobs for name in job.filenames))
		for job in jobs:
			self.assertLessEqual(command_units(job.arguments('C:\\Windows\\robocopy.exe', settings)), 300)

	def test_mixed_selection_maps_files_and_folders_to_exact_jobs(self):
		settings = Settings.load({})
		file = Source('C:\\source\\a.txt', 'a.txt', False, (1, 1, 0))
		folder = Source('C:\\source\\Photos', 'Photos', True, (1, 2, 0))
		jobs = build_jobs('C:\\source', 'D:\\target', (file, folder), 'robocopy.exe', settings)
		self.assertEqual(('a.txt',), jobs[0].filenames)
		self.assertEqual('C:\\source\\Photos', jobs[1].source)
		self.assertEqual('D:\\target\\Photos', jobs[1].destination)

	def test_robocopy_exit_bits_have_human_readable_descriptions(self):
		self.assertEqual('Copied files', exit_description(1))
		self.assertIn('extra destination entries', exit_description(3))
		self.assertIn('mismatches reported', exit_description(5))
		self.assertIn('Failed', exit_description(8))

	def test_prepare_refuses_destination_inside_selected_directory_before_writes(self):
		with tempfile.TemporaryDirectory() as temporary:
			root = Path(temporary)
			source, target = root / 'source', root / 'source' / 'folder' / 'nested'
			(source / 'folder').mkdir(parents=True)
			windows = types.SimpleNamespace(case_sensitive=lambda _path: False, filenames=directory_names)
			with patch.dict(sys.modules, {'robocopy_plugin.windows': windows}):
				planner = importlib.reload(importlib.import_module('robocopy_plugin.planner'))
				with self.assertRaisesRegex(ValueError, 'own subtree'):
					planner.prepare(as_url(source), (as_url(source / 'folder'),), str(target),
						'robocopy.exe', Settings.load({}))
			self.assertFalse(target.exists())

	def test_recheck_detects_replaced_source_and_cancellation(self):
		with tempfile.TemporaryDirectory() as temporary:
			root = Path(temporary)
			source = root / 'source'
			source.mkdir()
			entry = source / 'file.txt'
			entry.write_text('old')
			windows = types.SimpleNamespace(case_sensitive=lambda _path: False, filenames=file_names)
			with patch.dict(sys.modules, {'robocopy_plugin.windows': windows}):
				planner = importlib.reload(importlib.import_module('robocopy_plugin.planner'))
				plan = planner.prepare(as_url(source), (as_url(entry),), str(root / 'target'),
					'robocopy.exe', Settings.load({}))
				entry.unlink()
				entry.write_text('new')
				with self.assertRaisesRegex(ValueError, 'replaced'):
					planner.recheck(plan, plan.jobs[0])
				with self.assertRaises(InterruptedError):
					planner.remaining(plan.jobs[0].entries, lambda: (_ for _ in ()).throw(InterruptedError()))
