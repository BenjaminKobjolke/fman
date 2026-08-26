"""
The pure half of the background images a theme can carry: what the
"backgrounds" key in a theme file is allowed to say, which surface each
entry lands on, and where inside that surface it is drawn.

None of it touches Qt, so none of it needs a QApplication - the same
split as impl/model/icon_tint (pure) against impl/model/icon_provider
(Qt). The QPainter half lives in impl/view/backgrounds.py.
"""
from fman.impl.background import ANCHORS, DEFAULT_ANCHOR, DEFAULT_FIT, \
	DEFAULT_TARGET, FIT_MODES, Background, chrome_is_transparent, \
	focus_changes_pane, for_pane, for_window, normalize_backgrounds, \
	pane_is_transparent, place
from fman.impl.themes import load_backgrounds
from os.path import join
from tempfile import TemporaryDirectory
from unittest import TestCase

import json

def _touch(dir_, name):
	path = join(dir_, name)
	with open(path, 'wb') as f:
		f.write(b'not really a PNG')
	return path

class NormalizeBackgroundsTest(TestCase):

	"""
	The validator answers "unusable" with a drop, never a raise - the same
	contract as the _normalize_* functions in themes.py. A theme file is
	user input, and a typo in one must cost the image, not fman.
	"""

	def test_not_a_list(self):
		for value in (None, {}, 'x', 5, True):
			self.assertEqual((), normalize_backgrounds(value, '/themes'))
	def test_defaults(self):
		with TemporaryDirectory() as tmp:
			_touch(tmp, 'a.png')
			result = normalize_backgrounds([{'image': 'a.png'}], tmp)
			self.assertEqual(1, len(result))
			background = result[0]
			self.assertEqual(join(tmp, 'a.png'), background.path)
			self.assertEqual(DEFAULT_TARGET, background.target)
			self.assertEqual(DEFAULT_FIT, background.fit)
			self.assertEqual(DEFAULT_ANCHOR, background.anchor)
			self.assertEqual(1.0, background.opacity)
	def test_all_values_given(self):
		with TemporaryDirectory() as tmp:
			_touch(tmp, 'a.png')
			result = normalize_backgrounds([{
				'image': 'a.png', 'target': 'pane.1', 'fit': 'none',
				'anchor': 'bottom-right', 'opacity': 0.6
			}], tmp)
			self.assertEqual(
				(
					Background(
						join(tmp, 'a.png'), 'pane.1', 'none', 'bottom-right',
						0.6
					),
				),
				result
			)
	def test_absolute_path_is_kept(self):
		with TemporaryDirectory() as tmp:
			path = _touch(tmp, 'a.png')
			result = normalize_backgrounds([{'image': path}], '/elsewhere')
			self.assertEqual((path,), tuple(b.path for b in result))
	def test_missing_file_is_dropped(self):
		with TemporaryDirectory() as tmp:
			with self.assertLogs('fman.impl.background', 'WARNING'):
				self.assertEqual(
					(), normalize_backgrounds([{'image': 'nope.png'}], tmp)
				)
	def test_no_theme_dir_drops_relative_path(self):
		with self.assertLogs('fman.impl.background', 'WARNING'):
			self.assertEqual(
				(), normalize_backgrounds([{'image': 'a.png'}], None)
			)
	def test_unusable_entries_are_dropped(self):
		with TemporaryDirectory() as tmp:
			_touch(tmp, 'a.png')
			for entry in (
				'a.png', 5, None, [],
				{}, {'image': ''}, {'image': 5}, {'image': True},
				{'image': 'a.png', 'target': 'panel'},
				{'image': 'a.png', 'target': 'pane.'},
				{'image': 'a.png', 'target': 'pane.-1'},
				{'image': 'a.png', 'target': 'pane.x'},
				{'image': 'a.png', 'fit': 'squash'},
				{'image': 'a.png', 'anchor': 'middle'},
				{'image': 'a.png', 'opacity': 1.5},
				{'image': 'a.png', 'opacity': -0.1},
				{'image': 'a.png', 'opacity': 'half'},
				{'image': 'a.png', 'opacity': True}
			):
				# assertLogs doubles as the assertion that every drop is
				# reported, and keeps the warnings out of the test output.
				with self.assertLogs('fman.impl.background', 'WARNING'):
					self.assertEqual(
						(), normalize_backgrounds([entry], tmp), repr(entry)
					)
	def test_the_reason_names_the_key_and_what_was_allowed(self):
		with TemporaryDirectory() as tmp:
			_touch(tmp, 'a.png')
			with self.assertLogs('fman.impl.background', 'WARNING') as logs:
				normalize_backgrounds(
					[{'image': 'a.png', 'fit': 'fill'}], tmp
				)
		# "fill" is the name people reach for instead of "cover"; the
		# message has to say so rather than leave them with an image
		# that never appears.
		message = logs.output[0]
		self.assertIn("fit='fill'", message)
		self.assertIn('cover', message)
	def test_one_bad_entry_does_not_take_the_good_ones(self):
		with TemporaryDirectory() as tmp:
			_touch(tmp, 'a.png')
			with self.assertLogs('fman.impl.background', 'WARNING'):
				result = normalize_backgrounds(
					[{'image': 'gone.png'}, {'image': 'a.png'}], tmp
				)
			self.assertEqual(1, len(result))
	def test_every_fit_and_anchor_is_accepted(self):
		with TemporaryDirectory() as tmp:
			_touch(tmp, 'a.png')
			for fit in FIT_MODES:
				for anchor in ANCHORS:
					self.assertEqual(1, len(normalize_backgrounds(
						[{'image': 'a.png', 'fit': fit, 'anchor': anchor}], tmp
					)), '%s/%s' % (fit, anchor))

def _background(target):
	return Background('a.png', target, DEFAULT_FIT, DEFAULT_ANCHOR, 1.0)

class TargetsTest(TestCase):

	"""
	Which surface an entry lands on. Kept pure and in one place so
	"pane", "pane.<index>", "pane.active" and "pane.inactive" cannot
	drift apart between the painter and the transparency flag.
	"""

	def test_for_window(self):
		backgrounds = (_background('window'), _background('pane'))
		self.assertEqual((backgrounds[0],), for_window(backgrounds))
	def test_for_pane_takes_every_pane(self):
		background = _background('pane')
		for index in (0, 1, 7):
			for is_active in (True, False):
				self.assertEqual(
					(background,), for_pane((background,), index, is_active)
				)
	def test_for_pane_by_index(self):
		background = _background('pane.1')
		self.assertEqual((), for_pane((background,), 0, True))
		self.assertEqual((background,), for_pane((background,), 1, True))
	def test_for_pane_by_focus(self):
		active = _background('pane.active')
		inactive = _background('pane.inactive')
		self.assertEqual((active,), for_pane((active, inactive), 0, True))
		self.assertEqual((inactive,), for_pane((active, inactive), 0, False))
	def test_window_never_lands_on_a_pane(self):
		self.assertEqual((), for_pane((_background('window'),), 0, True))
	def test_order_is_kept(self):
		first, second = _background('pane'), _background('pane.0')
		self.assertEqual((first, second), for_pane((first, second), 0, True))

class TransparencyTest(TestCase):

	"""
	Whether a surface must stop painting its own opaque background. It
	deliberately does not depend on which pane has focus: a flag that
	flipped on every focus change would re-polish the widget every time
	the user switches panes.
	"""

	def test_nothing_is_opaque(self):
		self.assertFalse(pane_is_transparent((), 0))
		self.assertFalse(chrome_is_transparent(()))
	def test_own_image_makes_a_pane_transparent(self):
		backgrounds = (_background('pane.1'),)
		self.assertFalse(pane_is_transparent(backgrounds, 0))
		self.assertTrue(pane_is_transparent(backgrounds, 1))
	def test_focus_targets_do_not_flip_the_flag(self):
		for target in ('pane.active', 'pane.inactive'):
			self.assertTrue(pane_is_transparent((_background(target),), 0))
	def test_window_image_makes_everything_transparent(self):
		backgrounds = (_background('window'),)
		self.assertTrue(pane_is_transparent(backgrounds, 3))
		self.assertTrue(chrome_is_transparent(backgrounds))
	def test_pane_image_leaves_the_chrome_alone(self):
		self.assertFalse(chrome_is_transparent((_background('pane'),)))

class FocusChangesPaneTest(TestCase):

	"""
	Whether a pane switch is worth a repaint. The answer has to be no
	for every theme that places no focus-dependent image, or fman would
	repaint two panes on every move for nothing.
	"""

	def test_nothing_to_repaint(self):
		self.assertFalse(focus_changes_pane((), 0))
	def test_a_plain_pane_image_looks_the_same_either_way(self):
		for target in ('window', 'pane', 'pane.0'):
			self.assertFalse(
				focus_changes_pane((_background(target),), 0), target
			)
	def test_focus_targets_are_worth_a_repaint(self):
		for target in ('pane.active', 'pane.inactive'):
			self.assertTrue(
				focus_changes_pane((_background(target),), 0), target
			)
	def test_only_for_the_pane_it_names(self):
		backgrounds = (_background('pane.active'),)
		self.assertTrue(focus_changes_pane(backgrounds, 0))
		# "pane.active" is any pane, so every index answers the same.
		self.assertTrue(focus_changes_pane(backgrounds, 4))

class PlaceTest(TestCase):

	"""
	Where the image is drawn inside its surface. Sizes are in pixels and
	the result may hang outside the surface - that is what "cover" means.
	"""

	def test_stretch_ignores_aspect_ratio(self):
		self.assertEqual(
			(0, 0, 200, 200), place(100, 50, 200, 200, 'stretch', 'center')
		)
	def test_cover_fills_and_overhangs(self):
		self.assertEqual(
			(-100, 0, 400, 200), place(100, 50, 200, 200, 'cover', 'center')
		)
	def test_contain_fits_and_letterboxes(self):
		self.assertEqual(
			(0, 50, 200, 100), place(100, 50, 200, 200, 'contain', 'center')
		)
	def test_none_keeps_the_native_size(self):
		self.assertEqual(
			(100, 150, 100, 50),
			place(100, 50, 200, 200, 'none', 'bottom-right')
		)
	def test_tile_starts_at_the_origin(self):
		self.assertEqual(
			(0, 0, 100, 50), place(100, 50, 200, 200, 'tile', 'bottom-right')
		)
	def test_anchors(self):
		# A 100x50 image at its native size in a 300x250 surface leaves
		# 200x200 of slack, so each anchor lands on a round number.
		expected = {
			'top-left': (0, 0), 'top': (100, 0), 'top-right': (200, 0),
			'left': (0, 100), 'center': (100, 100), 'right': (200, 100),
			'bottom-left': (0, 200), 'bottom': (100, 200),
			'bottom-right': (200, 200)
		}
		self.assertEqual(set(ANCHORS), set(expected))
		for anchor, (x, y) in expected.items():
			self.assertEqual(
				(x, y, 100, 50), place(100, 50, 300, 250, 'none', anchor),
				anchor
			)
	def test_empty_image_draws_nothing(self):
		self.assertEqual(
			(0, 0, 0, 0), place(0, 0, 200, 200, 'cover', 'center')
		)

class LoadBackgroundsTest(TestCase):

	"""
	Reading the key out of a theme file. The paths in it are relative to
	the theme file that won, which is why this cannot go through
	_load_theme_value like the other five non-color keys.
	"""

	def _write_theme(self, dir_, name, contents):
		with open(join(dir_, name + '.json'), 'w') as f:
			json.dump(contents, f)
	def test_no_theme_file(self):
		with TemporaryDirectory() as tmp:
			self.assertEqual((), load_backgrounds('Nope', [tmp]))
	def test_no_key(self):
		with TemporaryDirectory() as tmp:
			self._write_theme(tmp, 'T', {'colors': {}})
			self.assertEqual((), load_backgrounds('T', [tmp]))
	def test_path_is_relative_to_the_theme_file(self):
		with TemporaryDirectory() as tmp:
			_touch(tmp, 'a.png')
			self._write_theme(tmp, 'T', {'backgrounds': [{'image': 'a.png'}]})
			self.assertEqual(
				(join(tmp, 'a.png'),),
				tuple(b.path for b in load_backgrounds('T', [tmp]))
			)
	def test_later_dirs_win(self):
		with TemporaryDirectory() as bundled, TemporaryDirectory() as user:
			_touch(bundled, 'a.png')
			_touch(user, 'b.png')
			self._write_theme(
				bundled, 'T', {'backgrounds': [{'image': 'a.png'}]}
			)
			self._write_theme(user, 'T', {'backgrounds': [{'image': 'b.png'}]})
			self.assertEqual(
				(join(user, 'b.png'),),
				tuple(b.path for b in load_backgrounds('T', [bundled, user]))
			)
