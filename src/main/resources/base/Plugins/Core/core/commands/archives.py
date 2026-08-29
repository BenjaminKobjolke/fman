"""Opening an archive as if it were a directory.

'Core Settings.json' maps a filename suffix to the scheme of the filesystem
that can read it ('.zip' -> 'zip://'), so which archives fman can enter is a
setting, not a hard-coded list. `ArchiveOpenListener` rewrites the URL of an
'open file' on a match, which is what makes Enter on a .zip navigate into it.
"""
from fman import DirectoryPaneListener, load_json
from fman.fs import is_dir
from fman.url import splitscheme
from os.path import basename

__all__ = ['ArchiveOpenListener']

def _get_handler_for_archive(file_name):
	settings = load_json('Core Settings.json', default={})
	archive_types = sorted(
		settings.get('archive_handlers', {}).items(),
		key=lambda tpl: -len(tpl[0])
	)
	for suffix, scheme in archive_types:
		if file_name.lower().endswith(suffix):
			return scheme

class ArchiveOpenListener(DirectoryPaneListener):
	def on_command(self, command_name, args):
		if command_name in ('open_file', 'open_directory'):
			url = args['url']
			try:
				scheme, path = splitscheme(url)
			except (KeyError, ValueError):
				return None
			if scheme == 'file://':
				new_scheme = _get_handler_for_archive(basename(path))
				if new_scheme:
					try:
						if is_dir(url):
							return None
					except OSError:
						return None
					new_args = dict(args)
					new_args['url'] = new_scheme + path
					return 'open_directory', new_args
