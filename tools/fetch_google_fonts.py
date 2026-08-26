"""
Vendors fman's bundled font families into
src/main/resources/base/Plugins/Core/Fonts.

Each family gets a directory named after the family Qt will register it
under, holding a Regular and (where upstream has one) a Bold .ttf plus the
upstream licence. That directory name is not a guess: it is read out of the
downloaded font's own `name` table, which is the same string QFontDatabase
reports and therefore the exact value a theme's "font" key has to carry.

Only static TTFs are taken. Qt 5 does not read variable-font axes, so a
variable file would give one weight with a synthesised bold, and the woff2
that @fontsource ships cannot be loaded by QFontDatabase at all.

Run it through tools/fetch_google_fonts.bat. Committing its output is the
point - fman must not need the network to draw text.
"""
from argparse import ArgumentParser
from json import loads
from os.path import abspath, basename, dirname, join
from shutil import rmtree
from urllib.parse import quote
from urllib.request import urlopen

import os
import struct

# The families fman bundles. Each is on Google Fonts under the SIL Open Font
# License; docs/THEMES.md lists which theme uses which.
FAMILIES = (
	'JetBrains Mono',
	'Fira Code',
	'IBM Plex Sans',
	# Not Inter: Google Fonts only ships its optical-size cuts, so the
	# family Qt registers is "Inter 18pt" - not a string to ask a theme
	# author to write, nor one to show in the command palette.
	'Public Sans',
	'Share Tech Mono',
	'Atkinson Hyperlegible'
)

# The two weights fman needs. Qt synthesises the rest, and shipping nine
# weights of six families to draw a file list would be absurd.
WEIGHTS = ('Regular', 'Bold')

_LIST_URL = 'https://fonts.google.com/download/list?family='
# The response is JSON behind an anti-hijacking prefix, so it does not parse
# until the first brace.
_JSON_PREFIX = ")]}'"

_ATTRIBUTION = """\
%s is vendored unchanged from Google Fonts:

    https://fonts.google.com/specimen/%s

fman bundles it so a theme can ask for it without the machine having it
installed - see docs/THEMES.md. It is used under the license reproduced
below.

----------------------------------------------------------------------

"""

def main():
	parser = ArgumentParser(description=__doc__)
	parser.add_argument(
		'--family', action='append', metavar='NAME',
		help='vendor only this family (repeatable; default: all of them)'
	)
	args = parser.parse_args()
	families = args.family or list(FAMILIES)
	dest_root = join(
		dirname(dirname(abspath(__file__))), 'src', 'main', 'resources',
		'base', 'Plugins', 'Core', 'Fonts'
	)
	for family in families:
		_vendor(family, dest_root)

def _vendor(family, dest_root):
	print('Fetching %s...' % family)
	manifest = _get_manifest(family)
	files = _pick_files(manifest, family)
	fonts = {weight: _get(url) for weight, url in files.items()}
	# The family Qt will report, read from the file rather than from the name
	# we asked Google for: they differ (Google's "Inter" ships as the optical
	# size "Inter 18pt"), and it is Qt's answer a theme has to match.
	qt_family = _read_family_name(fonts['Regular'])
	dest = join(dest_root, qt_family)
	# Rebuilt rather than merged, so a weight upstream drops cannot linger.
	if os.path.isdir(dest):
		rmtree(dest)
	os.makedirs(dest)
	for weight, data in fonts.items():
		with open(join(dest, weight + '.ttf'), 'wb') as f:
			f.write(data)
	_write_license(dest, family, manifest)
	print(
		'  %s -> %s (%s)'
		% (family, dest, ', '.join(sorted(fonts)))
	)

def _get_manifest(family):
	raw = _get(_LIST_URL + quote(family)).decode('utf-8')
	if raw.startswith(_JSON_PREFIX):
		raw = raw[len(_JSON_PREFIX):]
	return loads(raw)['manifest']

def _pick_files(manifest, family):
	"""
	The URL of each weight in WEIGHTS, keyed by weight. A family may ship its
	statics under static/ (JetBrains Mono) or at the top level (Share Tech
	Mono), and may offer several cuts of the same weight - condensed widths
	for IBM Plex Sans, optical sizes for Inter. The shortest file name is the
	plain cut in every case, which is the one fman wants.
	"""
	result = {}
	for weight in WEIGHTS:
		suffix = '-%s.ttf' % weight
		candidates = [
			ref for ref in manifest.get('fileRefs', [])
			if basename(ref['filename']).endswith(suffix)
		]
		if not candidates:
			# Not an error: Share Tech Mono has no bold, and Qt synthesises
			# one. Only a missing Regular means the family cannot be shipped.
			if weight == 'Regular':
				raise LookupError('%s has no static %s' % (family, weight))
			print('  %s has no %s upstream; Qt will synthesise it' % (
				family, weight
			))
			continue
		best = min(candidates, key=lambda r: (len(basename(r['filename'])),
											  r['filename']))
		result[weight] = best['url']
	return result

def _read_family_name(data):
	"""
	The family name in `data`'s sfnt `name` table. Name ID 16 (typographic
	family) wins over ID 1 (family) because that is the order Qt resolves
	them in: for a family with more than four weights, ID 1 carries a
	sub-family like "Inter Light" while ID 16 carries "Inter".
	"""
	num_tables = struct.unpack('>H', data[4:6])[0]
	name_table = None
	for i in range(num_tables):
		tag, _, offset, length = struct.unpack(
			'>4sIII', data[12 + i * 16:28 + i * 16]
		)
		if tag == b'name':
			name_table = (offset, length)
			break
	if name_table is None:
		raise LookupError('Font has no name table')
	start = name_table[0]
	count, string_offset = struct.unpack('>HH', data[start + 2:start + 6])
	strings = start + string_offset
	found = {}
	for i in range(count):
		record = start + 6 + i * 12
		platform, encoding, _, name_id, length, offset = \
			struct.unpack('>HHHHHH', data[record:record + 12])
		if name_id not in (1, 16):
			continue
		raw = data[strings + offset:strings + offset + length]
		# Platform 3 (Windows) is UTF-16BE; platform 1 (Mac) is single-byte.
		text = raw.decode('utf-16-be' if platform == 3 else 'latin-1', 'ignore')
		found.setdefault(name_id, text.strip())
	name = found.get(16) or found.get(1)
	if not name:
		raise LookupError('Font names no family')
	return name

def _write_license(dest, family, manifest):
	texts = [
		f['contents'] for f in manifest.get('files', [])
		if f['filename'].upper().startswith(('OFL', 'LICENSE'))
	]
	if not texts:
		raise LookupError('%s ships no license' % family)
	header = _ATTRIBUTION % (family, quote(family))
	with open(join(dest, 'LICENSE'), 'w', encoding='utf-8') as f:
		f.write(header + '\n\n'.join(texts))

def _get(url):
	with urlopen(url) as response:
		return response.read()

if __name__ == '__main__':
	main()
