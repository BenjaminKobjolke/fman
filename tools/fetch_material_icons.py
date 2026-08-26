"""
Vendors the Material Icon Theme into src/main/resources/base/Icons/Material.

Upstream (MIT) ships 1251 SVGs and a 450 KB VS Code icon-theme manifest. fman
needs neither in full: it has no language service and its panes have no
expanded state, so languageIds, folderNamesExpanded, rootFolderNames, light
and highContrast are all dead weight. This writes the slimmed manifest and
copies only the icons that manifest can actually name.

Run it through tools/fetch_material_icons.bat. Committing its output is the
point - fman must not need the network to draw an icon.
"""
from argparse import ArgumentParser
from io import BytesIO
from json import dump, loads
from os.path import abspath, dirname, join
from shutil import rmtree
from tarfile import open as taropen
from urllib.request import urlopen

import os

PACKAGE = 'material-icon-theme'
REGISTRY_URL = 'https://registry.npmjs.org/' + PACKAGE

# The keys fman reads. Everything else upstream ships is dead weight here -
# see the module docstring.
MANIFEST_KEYS = ('fileExtensions', 'fileNames', 'folderNames')
DEFAULT_KEYS = ('file', 'folder')

_TARBALL_ROOT = 'package'
_UPSTREAM_MANIFEST = _TARBALL_ROOT + '/dist/material-icons.json'
_UPSTREAM_ICONS = _TARBALL_ROOT + '/icons/'
_UPSTREAM_LICENSE = _TARBALL_ROOT + '/LICENSE'

_ATTRIBUTION = """\
The icons in this directory are the Material Icon Theme by Material
Extensions, vendored unchanged from the npm package "%s" (version %s):

    https://github.com/material-extensions/vscode-material-icon-theme

They are used under the MIT license reproduced below. fman ships them as the
optional "Material" icon set - see docs/THEMES.md.

----------------------------------------------------------------------

"""

def main():
	parser = ArgumentParser(description=__doc__)
	parser.add_argument(
		'--version', default='latest',
		help='the npm version to vendor (default: the latest release)'
	)
	args = parser.parse_args()
	dest = join(
		dirname(dirname(abspath(__file__))),
		'src', 'main', 'resources', 'base', 'Icons', 'Material'
	)
	version, tarball_url = _resolve_release(args.version)
	print('Fetching %s %s...' % (PACKAGE, version))
	with taropen(fileobj=BytesIO(_get(tarball_url))) as tarball:
		manifest = _slim(
			loads(_read(tarball, _UPSTREAM_MANIFEST).decode('utf-8')), version
		)
		missing = _extract_icons(tarball, manifest, join(dest, 'svg'))
		_prune(manifest, missing)
		_write_manifest(dest, manifest)
		_write_license(dest, version, tarball)
	print(
		'Wrote %d icons and %d mappings to %s'
		% (len(_icon_names(manifest)), _num_mappings(manifest), dest)
	)

def _resolve_release(version):
	release = loads(_get(REGISTRY_URL + '/' + version).decode('utf-8'))
	return release['version'], release['dist']['tarball']

def _get(url):
	with urlopen(url) as response:
		return response.read()

def _read(tarball, member):
	extracted = tarball.extractfile(member)
	if extracted is None:
		raise LookupError('%s is missing from the tarball' % member)
	with extracted:
		return extracted.read()

def _slim(upstream, version):
	"""
	`upstream`'s manifest reduced to the keys fman reads, plus the version it
	came from so the vendored copy says what it is.
	"""
	result = {'upstream_version': version}
	for key in DEFAULT_KEYS:
		result[key] = upstream[key]
	for key in MANIFEST_KEYS:
		# Lower-cased here rather than at every lookup: file names on disk
		# vary in case and the manifest is matched case-insensitively.
		result[key] = {
			name.lower(): icon for name, icon in upstream[key].items()
		}
	return result

def _num_mappings(manifest):
	return sum(len(manifest[key]) for key in MANIFEST_KEYS)

def _icon_names(manifest):
	result = set(manifest[key] for key in DEFAULT_KEYS)
	for key in MANIFEST_KEYS:
		result.update(manifest[key].values())
	return result

def _extract_icons(tarball, manifest, svg_dir):
	"""
	Writes every icon `manifest` names into `svg_dir`, and returns the names
	upstream does not actually ship. The published package maps a handful of
	names it has no file for (angular-resolver, folder-redis, ...); _prune
	drops those mappings so the manifest cannot promise a missing file.
	"""
	# Start from empty so an icon dropped upstream does not linger here and
	# keep a stale mapping working locally.
	if os.path.exists(svg_dir):
		rmtree(svg_dir)
	os.makedirs(svg_dir)
	missing = set()
	for name in sorted(_icon_names(manifest)):
		try:
			contents = _read(tarball, _UPSTREAM_ICONS + name + '.svg')
		except (KeyError, LookupError):
			missing.add(name)
			continue
		with open(join(svg_dir, name + '.svg'), 'wb') as f:
			f.write(contents)
	return missing

def _prune(manifest, missing):
	"""
	Drops the mappings pointing at an icon upstream does not ship. Such a
	mapping is dead weight: the lookup would find no file and fall back to
	the generic icon anyway, and test_icon_set.py asserts every name the
	manifest can produce has one.
	"""
	for key in DEFAULT_KEYS:
		if manifest[key] in missing:
			# The generic fallbacks have no fallback of their own.
			raise LookupError('upstream ships no %r icon' % manifest[key])
	dropped = 0
	for key in MANIFEST_KEYS:
		kept = {
			name: icon for name, icon in manifest[key].items()
			if icon not in missing
		}
		dropped += len(manifest[key]) - len(kept)
		manifest[key] = kept
	if dropped:
		print(
			'Dropped %d mapping(s) to %d icon(s) upstream does not ship: %s'
			% (dropped, len(missing), ', '.join(sorted(missing)))
		)

def _write_manifest(dest, manifest):
	with open(join(dest, 'manifest.json'), 'w') as f:
		dump(manifest, f, indent='\t', sort_keys=True)
		f.write('\n')

def _write_license(dest, version, tarball):
	upstream = _read(tarball, _UPSTREAM_LICENSE).decode('utf-8')
	with open(join(dest, 'LICENSE'), 'w', encoding='utf-8') as f:
		f.write(_ATTRIBUTION % (PACKAGE, version))
		f.write(upstream)

if __name__ == '__main__':
	main()
