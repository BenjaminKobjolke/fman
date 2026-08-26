from fman.impl.model.icon_set import DEFAULT_ICON_SET, IconSet, \
	is_valid_icon_set_name, list_icon_sets, load_icon_set
from json import dump
from os.path import dirname, isfile, join
from tempfile import TemporaryDirectory
from unittest import TestCase

import os

_BUNDLED_ICONS_DIR = join(
	dirname(dirname(dirname(dirname(dirname(dirname(__file__)))))),
	'main', 'resources', 'base', 'Icons'
)
_BUNDLED_SET = 'Material'

_MANIFEST = {
	'file': 'file',
	'folder': 'folder',
	'fileNames': {'dockerfile': 'docker'},
	'fileExtensions': {'ts': 'typescript', 'd.ts': 'typescript-def'},
	'folderNames': {'src': 'folder-src'}
}

class IconNameTest(TestCase):

	"""
	Which icon a file or folder maps to. The set is built by hand here so
	the rules are readable; BundledIconSetTest checks the real one.
	"""

	def test_extension(self):
		self.assertEqual('typescript', self._name('foo.ts'))
	def test_extension_is_case_insensitive(self):
		self.assertEqual('typescript', self._name('Foo.TS'))
	def test_longest_extension_wins(self):
		# The manifest has hundreds of multi-dot keys. Matching the shortest
		# suffix first would give every .d.ts file the plain TypeScript icon.
		self.assertEqual('typescript-def', self._name('foo.d.ts'))
	def test_file_name_beats_extension(self):
		self.assertEqual('docker', self._name('Dockerfile'))
	def test_unknown_file_falls_back(self):
		self.assertEqual('file', self._name('foo.unheard-of'))
	def test_folder_name(self):
		self.assertEqual('folder-src', self._name('src', is_dir=True))
	def test_unknown_folder_falls_back(self):
		self.assertEqual('folder', self._name('whatever', is_dir=True))
	def test_folder_does_not_match_file_rules(self):
		# A directory called "foo.ts" is still a directory.
		self.assertEqual('folder', self._name('foo.ts', is_dir=True))
	def test_missing_manifest_section(self):
		# A hand-written manifest only fills in the parts it cares about.
		icon_set = IconSet('Partial', 'dir', {'file': 'file'})
		self.assertEqual('file', icon_set.icon_name('foo.ts', False))
		self.assertIsNone(icon_set.icon_name('foo', True))
	def _name(self, file_name, is_dir=False):
		return IconSet('Test', 'dir', _MANIFEST).icon_name(file_name, is_dir)

class IconPathTest(TestCase):

	def setUp(self):
		super().setUp()
		self._dir = TemporaryDirectory()
		self.addCleanup(self._dir.cleanup)
		os.makedirs(join(self._dir.name, 'svg'))
		self._write('file.svg')
		self._icon_set = IconSet('Test', self._dir.name, _MANIFEST)

	def test_existing_icon(self):
		self.assertTrue(isfile(self._icon_set.icon_path('file')))
	def test_icon_the_set_does_not_ship(self):
		# Not an error: it reads as "no icon", so the caller falls back to
		# the OS the same way it does for a name the manifest never mentions.
		self.assertIsNone(self._icon_set.icon_path('typescript'))
	def test_traversal_is_refused(self):
		for name in ('../../etc/passwd', '..\\..\\secrets', '/etc/passwd'):
			with self.subTest(name):
				self.assertIsNone(self._icon_set.icon_path(name))
	def test_no_name(self):
		self.assertIsNone(self._icon_set.icon_path(None))
	def test_icon_file_composes_name_and_path(self):
		self.assertTrue(isfile(self._icon_set.icon_file('foo.unheard-of', False)))
		self.assertIsNone(self._icon_set.icon_file('foo.ts', False))
	def _write(self, name):
		with open(join(self._dir.name, 'svg', name), 'w') as f:
			f.write('<svg/>')

class IconSetNameTest(TestCase):

	def test_usable(self):
		for name in ('Material', 'My Icons', 'a-b_c.1'):
			with self.subTest(name):
				self.assertTrue(is_valid_icon_set_name(name))
	def test_unusable(self):
		# A name becomes a directory under the icon dirs, so anything that
		# could climb out of them has to be refused before it is joined.
		for name in ('', '.', '..', '/etc', 'a/b', 'a\\b', '\\', 5, None, True):
			with self.subTest(name):
				self.assertFalse(is_valid_icon_set_name(name))

class LoadIconSetTest(TestCase):

	def setUp(self):
		super().setUp()
		self._bundled = TemporaryDirectory()
		self._user = TemporaryDirectory()
		self.addCleanup(self._bundled.cleanup)
		self.addCleanup(self._user.cleanup)
		self._dirs = [self._bundled.name, self._user.name]

	def test_lists_the_default_even_without_dirs(self):
		self.assertEqual([DEFAULT_ICON_SET], list_icon_sets([]))
	def test_lists_sets_from_all_dirs(self):
		self._create(self._bundled.name, 'Material')
		self._create(self._user.name, 'Mine')
		self.assertEqual(
			['Material', 'Mine', DEFAULT_ICON_SET], list_icon_sets(self._dirs)
		)
	def test_a_dir_without_a_manifest_is_not_a_set(self):
		os.makedirs(join(self._bundled.name, 'Empty'))
		self.assertEqual([DEFAULT_ICON_SET], list_icon_sets(self._dirs))
	def test_loads(self):
		self._create(self._bundled.name, 'Material')
		self.assertEqual('Material', load_icon_set('Material', self._dirs).name)
	def test_user_set_shadows_bundled_one(self):
		self._create(self._bundled.name, 'Material', {'file': 'bundled'})
		self._create(self._user.name, 'Material', {'file': 'user'})
		icon_set = load_icon_set('Material', self._dirs)
		self.assertEqual('user', icon_set.icon_name('foo', False))
	def test_default_has_no_set(self):
		# "System" is the absence of a set, not a set called System.
		self.assertIsNone(load_icon_set(DEFAULT_ICON_SET, self._dirs))
	def test_missing_set(self):
		self.assertIsNone(load_icon_set('Nope', self._dirs))
	def test_unusable_name(self):
		self.assertIsNone(load_icon_set('../elsewhere', self._dirs))
	def test_broken_manifest_is_not_fatal(self):
		# A broken set must cost you that set, not fman's startup.
		os.makedirs(join(self._bundled.name, 'Broken'))
		with open(join(self._bundled.name, 'Broken', 'manifest.json'), 'w') as f:
			f.write('{not json')
		self.assertIsNone(load_icon_set('Broken', self._dirs))
	def test_manifest_that_is_not_an_object(self):
		self._create(self._bundled.name, 'Odd', [])
		self.assertIsNone(load_icon_set('Odd', self._dirs))
	def _create(self, dir_, name, manifest=None):
		os.makedirs(join(dir_, name), exist_ok=True)
		with open(join(dir_, name, 'manifest.json'), 'w') as f:
			dump(_MANIFEST if manifest is None else manifest, f)

class BundledIconSetTest(TestCase):

	"""
	The vendoring guard. tools/fetch_material_icons.py writes both the
	manifest and the SVGs; if it half-ran, the manifest promises icons that
	are not there and every one of those files silently gets the OS icon.
	"""

	def setUp(self):
		super().setUp()
		self._icon_set = load_icon_set(_BUNDLED_SET, [_BUNDLED_ICONS_DIR])

	def test_is_bundled(self):
		self.assertIn(_BUNDLED_SET, list_icon_sets([_BUNDLED_ICONS_DIR]))
		self.assertIsNotNone(self._icon_set)
	def test_every_promised_icon_exists(self):
		missing = sorted(
			name for name in self._icon_names()
			if self._icon_set.icon_path(name) is None
		)
		self.assertEqual([], missing)
	def test_known_files_and_folders(self):
		for file_name, is_dir, expected in (
			('main.py', False, 'python'),
			('Foo.TS', False, 'typescript'),
			('Dockerfile', False, 'docker'),
			('nothing.like-this', False, 'file'),
			('src', True, 'folder-src'),
			('nothing-like-this', True, 'folder')
		):
			with self.subTest(file_name):
				self.assertEqual(
					expected, self._icon_set.icon_name(file_name, is_dir)
				)
	def _icon_names(self):
		manifest = self._icon_set._manifest
		result = {manifest['file'], manifest['folder']}
		for key in ('fileExtensions', 'fileNames', 'folderNames'):
			result.update(manifest[key].values())
		return result
