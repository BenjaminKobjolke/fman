"""
Reading a file for the text viewer (core/textviewer.py): the byte cap,
UTF-8-with-replacement decoding for display, and the editability check that
decides whether Save is offered at all. Split out of core/textviewer.py to
stay under the project's 300-line file cap. Pure (no Qt) throughout.
"""

# Cap how much of a file we read, so viewing a huge/binary-ish file can't
# freeze the UI:
MAX_VIEW_BYTES = 2 * 1024 * 1024

# How much of a file is_text_file() sniffs to decide binary vs. text.
SNIFF_BYTES = 8192

def is_text_file(path):
	"""
	Cheap binary/text sniff used to decide whether the internal viewer should
	touch `path` at all (see ViewFile/OpenOrView in core/commands/opening.py)
	rather than routing it to the text viewer, which would otherwise render
	.exe/.zip/etc. as garbled replacement characters. Reads the first chunk
	and calls anything containing a NUL byte binary — avoids maintaining an
	extension whitelist.
	# ponytail: NUL-byte heuristic; UTF-16 text reads as binary. Add an
	# encoding probe only if that turns out to matter.
	"""
	try:
		with open(path, 'rb') as f:
			chunk = f.read(SNIFF_BYTES)
	except OSError:
		return False
	return b'\x00' not in chunk

def read_capped(path):
	"""
	Reads up to MAX_VIEW_BYTES of `path`. Returns (data, truncated) so
	callers can both render a preview (read_text_for_view) and decide
	whether writing the buffer back is safe (is_editable) from the same read.
	"""
	with open(path, 'rb') as f:
		data = f.read(MAX_VIEW_BYTES + 1)
	truncated = len(data) > MAX_VIEW_BYTES
	if truncated:
		data = data[:MAX_VIEW_BYTES]
	return data, truncated

def decode_for_display(data, truncated):
	"""
	Decodes bytes as UTF-8 with errors replaced rather than guessing an
	encoding, and appends a truncation notice if the file was larger than
	the cap. Shared by the initial load (read_text_for_view) and reverting
	an open buffer (PaneTextView._revert).
	"""
	text = data.decode('utf-8', errors='replace')
	if truncated:
		text += '\n\n[... truncated, file is larger than %d MB ...]' % (
			MAX_VIEW_BYTES // (1024 * 1024)
		)
	return text

def is_editable(data, truncated):
	"""
	Whether it's safe to let the buffer be edited and saved back. False if
	the file was truncated (saving would chop off the untouched rest) or if
	it isn't strict UTF-8 (decode_for_display's errors='replace' is fine for
	display but lossy for a save).
	"""
	if truncated:
		return False
	try:
		data.decode('utf-8')
	except UnicodeDecodeError:
		return False
	return True

def load_for_view(path):
	"""
	The full load pipeline for `path`: (display_text, editable). Shared by
	PaneTextView's initial load (show_text_viewer) and Revert
	(PaneTextView._revert) so both read the file, decode it, and decide
	editability from the exact same bytes in one place rather than repeating
	the three-call sequence at each call site.
	"""
	data, truncated = read_capped(path)
	return decode_for_display(data, truncated), is_editable(data, truncated)

def read_text_for_view(path):
	"""Reads and decodes `path` for display only. See load_for_view for the
	combined read+decode+editability pipeline used by the viewer itself."""
	text, _editable = load_for_view(path)
	return text
