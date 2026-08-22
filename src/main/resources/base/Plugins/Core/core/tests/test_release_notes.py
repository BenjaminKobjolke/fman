from core.release_notes import (
	_candidate_release_dirs, first_existing_dir, list_releases, load_release,
	render_notes,
)
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import json
import os

def _make_release_dir(root, name, files):
	release_dir = Path(root) / name
	release_dir.mkdir()
	for filename, data in files.items():
		with open(release_dir / filename, 'w', encoding='utf-8') as f:
			json.dump(data, f)
	return release_dir

class FirstExistingDirTest(TestCase):
	def test_returns_first_existing_candidate(self):
		with TemporaryDirectory() as tmp:
			existing = Path(tmp) / 'exists'
			existing.mkdir()
			missing = Path(tmp) / 'missing'
			self.assertEqual(
				existing, first_existing_dir([missing, existing])
			)

	def test_returns_none_when_nothing_exists(self):
		with TemporaryDirectory() as tmp:
			missing_a = Path(tmp) / 'a'
			missing_b = Path(tmp) / 'b'
			self.assertIsNone(first_existing_dir([missing_a, missing_b]))

class CandidateReleaseDirsTest(TestCase):
	def test_skips_dev_source_when_path_too_shallow(self):
		# An installed/frozen path (e.g. under Program Files) doesn't have 7
		# parents. Indexing that used to raise IndexError on every launch
		# (see docs/CREATE_NEW_RELEASE.md).
		installed = Path(
			'C:/Program Files (x86)/fman/Plugins/Core/core/release_notes.py'
		)
		candidates = _candidate_release_dirs(installed)
		self.assertEqual(
			[Path('C:/Program Files (x86)/fman/release_notes')], candidates
		)

	def test_includes_dev_source_when_path_deep_enough(self):
		deep = Path('/'.join(['x'] * 12)) / 'core' / 'release_notes.py'
		candidates = _candidate_release_dirs(deep)
		self.assertEqual(2, len(candidates))
		self.assertEqual(deep.parents[3] / 'release_notes', candidates[0])
		self.assertEqual(deep.parents[7] / 'release_notes', candidates[1])

class ListReleasesTest(TestCase):
	def test_sorts_newest_first_by_version_then_build(self):
		with TemporaryDirectory() as tmp:
			_make_release_dir(tmp, '1.7.4_0', {'en.json': {}})
			_make_release_dir(tmp, '1.7.5_1', {'en.json': {}})
			_make_release_dir(tmp, '1.7.5_9', {'en.json': {}})
			_make_release_dir(tmp, '1.7.5_10', {'en.json': {}})
			releases = list_releases(tmp)
			self.assertEqual(
				['1.7.5_10', '1.7.5_9', '1.7.5_1', '1.7.4_0'],
				['%s_%d' % (version, build) for version, build, _ in releases]
			)

	def test_ignores_folders_that_do_not_match_version_build_pattern(self):
		with TemporaryDirectory() as tmp:
			_make_release_dir(tmp, '1.7.5_1', {'en.json': {}})
			os.mkdir(os.path.join(tmp, 'not_a_release'))
			releases = list_releases(tmp)
			self.assertEqual(1, len(releases))
			self.assertEqual('1.7.5', releases[0][0])
			self.assertEqual(1, releases[0][1])

class LoadReleaseTest(TestCase):
	def test_loads_requested_locale_when_present(self):
		with TemporaryDirectory() as tmp:
			release_dir = _make_release_dir(tmp, '1.7.5_1', {
				'en.json': {'title': 'English'},
				'de.json': {'title': 'Deutsch'},
			})
			data = load_release(release_dir, 'de')
			self.assertEqual('Deutsch', data['title'])

	def test_falls_back_to_en_when_locale_missing(self):
		with TemporaryDirectory() as tmp:
			release_dir = _make_release_dir(tmp, '1.7.5_1', {
				'en.json': {'title': 'English'},
			})
			data = load_release(release_dir, 'fr')
			self.assertEqual('English', data['title'])

class RenderNotesTest(TestCase):
	def test_renders_title_version_date_and_bulleted_notes(self):
		text = render_notes({
			'version': '1.7.5',
			'build': 1,
			'date': '2026-08-22',
			'title': 'New text viewer',
			'notes': ['First change', 'Second change'],
		})
		self.assertEqual(
			'New text viewer\n'
			'1.7.5_1 — 2026-08-22\n'
			'\n'
			'• First change\n'
			'• Second change',
			text
		)
