"""
Pure (no Qt) helpers for the "Release Notes" command
(core/commands/release_notes.py): locating the bundled release_notes/ folder,
listing releases newest-first, loading a release's notes with locale
fallback, and rendering them as plain text for the pane's text viewer
(core.textviewer.show_text_in_viewer). Split out of the command module so the
parsing/sorting/fallback logic is testable without Qt or a live fman
instance. See docs/CREATE_NEW_RELEASE.md for the release_notes/ layout and
JSON schema this reads.
"""
from pathlib import Path

import json
import re

# '<version>_<build>' folder name, e.g. '1.7.5_1'. Version is dotted semver
# (digits only per segment); build is a plain integer.
_RELEASE_DIR_RE = re.compile(r'^(\d+(?:\.\d+)*)_(\d+)$')

def first_existing_dir(candidates):
	"""
	Returns the first of `candidates` (an iterable of Path) that exists as a
	directory, or None if none do. Split out from release_notes_dir() so the
	"pick the first existing candidate" logic is testable without touching
	__file__-derived paths.
	"""
	for candidate in candidates:
		if candidate.is_dir():
			return candidate
	return None

def release_notes_dir():
	"""
	Locates the bundled release_notes/ folder. Checked in order:
	1. Next to this plugin (three levels up from this file) - where fbs
	   places it both in the frozen build (target/fman/release_notes, see
	   docs/CREATE_NEW_RELEASE.md #4) and in the bundled source tree
	   (src/main/resources/base/release_notes) once the freeze-time copy has
	   run, since both layouts put Plugins/Core's parent directly next to
	   release_notes/.
	2. The project root's own release_notes/ - so running from source
	   *before* that copy step (plain dev, no freeze yet) still finds the
	   release notes authored there.
	Returns None if neither exists (e.g. a checkout with no release notes
	authored yet).
	"""
	this_file = Path(__file__).resolve()
	bundled = this_file.parents[3] / 'release_notes'
	dev_source = this_file.parents[7] / 'release_notes'
	return first_existing_dir([bundled, dev_source])

def list_releases(release_dir):
	"""
	Lists the releases in `release_dir`, newest first. Each entry is
	(version_str, build_int, folder_path). Folder names that don't match
	'<version>_<build>' are skipped. Sorting is numeric on both the dotted
	version and the build (never a plain string sort - '1.7.5_10' must sort
	newer than '1.7.5_9', which a string compare would get backwards).
	"""
	releases = []
	for entry in Path(release_dir).iterdir():
		if not entry.is_dir():
			continue
		match = _RELEASE_DIR_RE.match(entry.name)
		if not match:
			continue
		version_str, build_str = match.groups()
		releases.append((version_str, int(build_str), entry))
	releases.sort(key=lambda r: (_version_tuple(r[0]), r[1]), reverse=True)
	return releases

def _version_tuple(version_str):
	return tuple(int(part) for part in version_str.split('.'))

def load_release(release_dir, locale_code):
	"""
	Loads the release notes JSON (docs/CREATE_NEW_RELEASE.md schema) for
	`locale_code` from `release_dir`, falling back to en.json when that
	locale wasn't translated (or hasn't been generated yet) for this
	release - per docs/CREATE_NEW_RELEASE.md, en.json is always authored.
	"""
	release_dir = Path(release_dir)
	locale_file = release_dir / ('%s.json' % locale_code)
	if not locale_file.is_file():
		locale_file = release_dir / 'en.json'
	with open(locale_file, 'r', encoding='utf-8') as f:
		return json.load(f)

def render_notes(data):
	"""
	Renders a loaded release's data as the plain text shown in the viewer
	(core.textviewer.show_text_in_viewer) - title, '<version>_<build> — date',
	then one bullet per entry in the 'notes' array.
	"""
	lines = [
		data['title'],
		'%s_%d — %s' % (data['version'], data['build'], data['date']),
		'',
	]
	lines += ['• %s' % note for note in data['notes']]
	return '\n'.join(lines)
