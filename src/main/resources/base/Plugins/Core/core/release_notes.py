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

# Plain semantic versions and legacy '<version>_<build>' folder names are
# both shipped in release_notes/.
_RELEASE_DIR_RE = re.compile(r'^(\d+(?:\.\d+)*)(?:_(\d+))?$')

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

def _candidate_release_dirs(this_file):
	"""
	Candidate release_notes/ locations for `this_file` (this module's own
	resolved path), checked in order - see release_notes_dir(). Split out so
	the path arithmetic is testable without patching __file__: an
	installed/frozen path (e.g. under Program Files) has far fewer parents
	than the dev source tree, so the dev-source candidate is only included
	when it's actually computable - indexing a too-short .parents raises
	IndexError, which used to crash every command-palette lookup on an
	installed build (see docs/CREATE_NEW_RELEASE.md).
	"""
	candidates = [this_file.parents[3] / 'release_notes']
	if len(this_file.parents) > 7:
		candidates.append(this_file.parents[7] / 'release_notes')
	return candidates

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
	   release notes authored there. Only checked when this_file is deep
	   enough for that to be a valid path (see _candidate_release_dirs).
	Returns None if no candidate exists (e.g. a checkout with no release
	notes authored yet).
	"""
	this_file = Path(__file__).resolve()
	return first_existing_dir(_candidate_release_dirs(this_file))

def list_releases(release_dir):
	"""
	Lists the releases in `release_dir`, newest first. Each entry is
	(folder_label, build_int, folder_path). Folder names that don't match a
	plain or legacy release label are skipped. Sorting is numeric on both the
	dotted version and legacy build number.
	"""
	releases = []
	for entry in Path(release_dir).iterdir():
		if not entry.is_dir():
			continue
		parsed = parse_label(entry.name)
		if parsed is None:
			continue
		releases.append((entry.name, parsed[1], entry))
	releases.sort(key=lambda release: parse_label(release[0]), reverse=True)
	return releases

def parse_label(label):
	"""Return the numeric release and build for a public release label."""
	match = _RELEASE_DIR_RE.fullmatch(label)
	if match is None:
		return None
	return _version_tuple(match.group(1)), int(match.group(2) or 0)

def list_bundled_releases():
	"""List the release notes shipped with this installation."""
	release_dir = release_notes_dir()
	return list_releases(release_dir) if release_dir else []

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

def render_notes(data, label=None):
	"""
	Renders loaded release data as plain text for the viewer. `label` is the
	release folder name, preserving legacy build suffixes when present.
	"""
	lines = [
		data['title'],
		'%s — %s' % (label or data['version'], data['date']),
		'',
	]
	lines += ['• %s' % note for note in data['notes']]
	return '\n'.join(lines)
