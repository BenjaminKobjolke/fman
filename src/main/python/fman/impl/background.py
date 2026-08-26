"""
The background images a theme can place behind fman's UI: what the
"backgrounds" key in a theme file may say, which surface each entry
lands on, and where inside that surface the image is drawn.

Free of Qt on purpose, so it can be tested without a QApplication - the
same split as impl/model/icon_tint against impl/model/icon_provider. The
QPainter half is impl/view/backgrounds.py, which owns the pixmaps and
the transparency flag; this half owns the rules. See docs/THEMES.md.
"""
from collections import namedtuple
from os.path import isabs, isfile, join, normpath

import logging

_LOG = logging.getLogger(__name__)

# The surfaces an entry may name. "pane" is every pane; "pane.<index>"
# is one of them, counted from the left the way _OpenInPaneCommand and
# ShowVolumes already count them; "pane.active"/"pane.inactive" pick by
# focus instead of position.
WINDOW = 'window'
PANE = 'pane'
ACTIVE_PANE = 'pane.active'
INACTIVE_PANE = 'pane.inactive'
_PANE_INDEX_PREFIX = PANE + '.'

# How the image is sized to its surface. "none" is the one that does not
# scale at all - it is what docks artwork into a corner at the size it
# was drawn at.
COVER = 'cover'
TILE = 'tile'
FIT_MODES = (COVER, 'contain', 'stretch', TILE, 'none')

# Where the slack between image and surface goes, as a fraction of it.
ANCHORS = {
	'top-left': (0.0, 0.0), 'top': (0.5, 0.0), 'top-right': (1.0, 0.0),
	'left': (0.0, 0.5), 'center': (0.5, 0.5), 'right': (1.0, 0.5),
	'bottom-left': (0.0, 1.0), 'bottom': (0.5, 1.0), 'bottom-right': (1.0, 1.0)
}

# What an entry that names none of them asks for. "window" and "cover"
# together are the plain wallpaper every other file manager means by a
# background image, so the shortest possible entry - just an image - is
# the one people expect.
DEFAULT_TARGET = WINDOW
DEFAULT_FIT = COVER
DEFAULT_ANCHOR = 'center'
DEFAULT_IMAGE_OPACITY = 1.0

class Background(
	namedtuple('Background', ('path', 'target', 'fit', 'anchor', 'opacity'))
):
	"""
	One image a theme places, with everything needed to draw it: an
	absolute path, the surface it belongs to, and how it is sized,
	positioned and blended there. A value object rather than the raw
	dict out of the theme file, so a missing key cannot read as None
	somewhere far away from the file that omitted it.
	"""

def normalize_backgrounds(value, theme_dir):
	"""
	The `backgrounds` value of a theme file as Backgrounds, with every
	entry fman cannot use dropped. `theme_dir` is the directory of the
	theme file the value came from; relative image paths resolve against
	it, and None means there is no such directory (so only absolute
	paths survive).

	Drops rather than raises, like the _normalize_* validators in
	themes.py: a theme file is user input, and a typo in one must cost
	the image, not the ability to start fman.
	"""
	if not isinstance(value, list):
		return ()
	return tuple(filter(None, (
		_normalize_background(entry, theme_dir) for entry in value
	)))

def for_window(backgrounds):
	"""
	The ones drawn behind the whole window, in the order the theme lists
	them - a later entry draws on top of an earlier one.
	"""
	return tuple(b for b in backgrounds if b.target == WINDOW)

def for_pane(backgrounds, index, is_active):
	"""
	The ones drawn behind the pane at `index`, given whether it
	currently has focus. Resolved per repaint rather than stored,
	because `is_active` changes as the user moves between panes.
	"""
	return tuple(
		b for b in backgrounds if _is_pane_target(b.target, index, is_active)
	)

def pane_is_transparent(backgrounds, index):
	"""
	Whether the pane at `index` must stop painting its own opaque
	background - either something of its own is drawn behind it, or the
	window image is and would otherwise be hidden.

	Deliberately not a function of focus, unlike for_pane: a flag that
	flipped as the user switched panes would re-polish the widget every
	time, and a pane that is transparent while focused and opaque while
	not would flash its theme color on every move.
	"""
	return bool(
		for_pane(backgrounds, index, True) or
		for_pane(backgrounds, index, False) or
		for_window(backgrounds)
	)

def focus_changes_pane(backgrounds, index):
	"""
	Whether the pane at `index` draws something different depending on
	whether it has focus - i.e. whether a focus change there is worth a
	repaint at all. False for every theme that places no "pane.active"
	or "pane.inactive" image, which is what keeps an fman whose theme
	places none repainting exactly as often on a pane switch as it did
	before backgrounds existed.
	"""
	return for_pane(backgrounds, index, True) != \
		for_pane(backgrounds, index, False)

def chrome_is_transparent(backgrounds):
	"""
	Whether the column headers, the location bars and the status bar
	must stop painting their own backgrounds. Only a window image runs
	behind them - a pane image stays inside its pane, so the strips keep
	their theme colors and the file names above them stay readable.
	"""
	return bool(for_window(backgrounds))

def place(image_w, image_h, rect_w, rect_h, fit, anchor):
	"""
	Where to draw an `image_w` x `image_h` image inside an
	`rect_w` x `rect_h` surface, as (x, y, w, h) relative to the
	surface's top left. For COVER the result is deliberately larger than
	the surface and x/y go negative: that is what cropping to fill means.
	TILE answers the image's own size at the origin - the caller repeats
	it, so an anchor has nothing to say about it.
	"""
	if image_w <= 0 or image_h <= 0:
		return (0, 0, 0, 0)
	if fit == 'stretch':
		return (0, 0, rect_w, rect_h)
	if fit == TILE:
		return (0, 0, image_w, image_h)
	if fit == 'none':
		width, height = image_w, image_h
	else:
		scales = (rect_w / image_w, rect_h / image_h)
		scale = max(scales) if fit == COVER else min(scales)
		width = max(1, round(image_w * scale))
		height = max(1, round(image_h * scale))
	x_factor, y_factor = ANCHORS[anchor]
	return (
		round((rect_w - width) * x_factor),
		round((rect_h - height) * y_factor),
		width, height
	)

def _normalize_background(entry, theme_dir):
	# Every rejection is logged. Dropping the entry is the right
	# behaviour - a typo must not stop fman from starting - but on its
	# own it leaves the theme author with an image that simply never
	# appears and nothing to go on. "fit": "fill" instead of "cover" is
	# the first mistake this feature saw in the wild.
	if not isinstance(entry, dict):
		return _drop(entry, 'not a JSON object')
	path = _normalize_path(entry.get('image'), theme_dir)
	if path is None:
		return _drop(entry, 'no readable "image" file')
	values = (
		('target', _normalize_choice(
			entry.get('target'), DEFAULT_TARGET, _is_target
		), 'window, pane, pane.<index>, pane.active, pane.inactive'),
		('fit', _normalize_choice(
			entry.get('fit'), DEFAULT_FIT, FIT_MODES.__contains__
		), ', '.join(FIT_MODES)),
		('anchor', _normalize_choice(
			entry.get('anchor'), DEFAULT_ANCHOR, ANCHORS.__contains__
		), ', '.join(sorted(ANCHORS))),
		('opacity', _normalize_opacity(entry.get('opacity')), '0.0 to 1.0')
	)
	for key, value, allowed in values:
		if value is None:
			return _drop(
				entry, '%s=%r is not one of: %s'
				% (key, entry.get(key), allowed)
			)
	return Background(path, *(value for _, value, _ in values))

def _drop(entry, reason):
	_LOG.warning('Ignoring theme background %r: %s.', entry, reason)
	return None

def _normalize_path(value, theme_dir):
	# Deliberately no check against separators or "..", unlike
	# icon_set.is_valid_icon_set_name: that guards a *name* which is
	# then pasted into a path fman owns, whereas this value *is* the
	# path and pointing it at any file on the machine is the feature.
	if isinstance(value, bool) or not isinstance(value, str) or not value:
		return None
	if isabs(value):
		path = value
	elif theme_dir is None:
		return None
	else:
		path = normpath(join(theme_dir, value))
	# Whether Qt can decode the file is not decided here: the painter
	# answers that, and answers a null pixmap - the same as asking for
	# no image at all.
	return path if isfile(path) else None

def _normalize_choice(value, default, is_valid):
	if value is None:
		return default
	return value if isinstance(value, str) and is_valid(value) else None

def _normalize_opacity(value):
	# Booleans are rejected explicitly for the same reason as in
	# themes._normalize_opacity: True is an int in Python and would
	# otherwise read as "fully opaque".
	if value is None:
		return DEFAULT_IMAGE_OPACITY
	if isinstance(value, bool) or not isinstance(value, (int, float)):
		return None
	return float(value) if 0.0 <= value <= 1.0 else None

def _is_target(value):
	if value in (WINDOW, PANE, ACTIVE_PANE, INACTIVE_PANE):
		return True
	return _pane_index(value) is not None

def _is_pane_target(target, index, is_active):
	if target == PANE:
		return True
	if target == ACTIVE_PANE:
		return is_active
	if target == INACTIVE_PANE:
		return not is_active
	return _pane_index(target) == index

def _pane_index(target):
	"""
	The pane "pane.<index>" names, or None if `target` is not that shape.
	isdigit() rather than int(): it rejects "-1" and "+1", which would
	otherwise parse into a pane that cannot exist.
	"""
	if not isinstance(target, str) or not target.startswith(_PANE_INDEX_PREFIX):
		return None
	suffix = target[len(_PANE_INDEX_PREFIX):]
	return int(suffix) if suffix.isdigit() else None
