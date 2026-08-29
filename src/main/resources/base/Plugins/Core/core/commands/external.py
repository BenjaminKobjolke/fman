"""Handing a directory - or a preview of a file - to another program.

Every command here refuses anything but file:// URLs: a terminal, the native
file manager and Quick Look all take a path on disk, and there is nothing to
give them for a location that only exists inside fman (a zip://, say).
"""
from core.commands.util import chosen_files, is_file_url
from core.os_ import open_native_file_manager, open_terminal_in_directory
from fman import DirectoryPaneCommand, PLATFORM, show_alert
from fman.fs import iterdir
from fman.url import as_human_readable, join, splitscheme
from subprocess import Popen, DEVNULL

__all__ = [
	'CompareDirectories', 'OpenNativeFileManager', 'OpenTerminal'
]
if PLATFORM == 'Mac':
	__all__.append('QuickLook')

class OpenTerminal(DirectoryPaneCommand):

	aliases = ('Terminal',)

	def __call__(self):
		scheme, path = splitscheme(self.pane.get_path())
		if scheme != 'file://':
			show_alert(
				"Can currently open the terminal only in local directories."
			)
			return
		open_terminal_in_directory(path)

class OpenNativeFileManager(DirectoryPaneCommand):
	def __call__(self):
		url = self.pane.get_path()
		scheme = splitscheme(url)[0]
		if scheme != 'file://':
			if PLATFORM == 'Mac':
				native_fm = 'Finder'
			elif PLATFORM == 'Windows':
				native_fm = 'Explorer'
			else:
				native_fm = 'your native file manager'
			show_alert("Cannot open %s in %s" % (native_fm, scheme))
			return
		open_native_file_manager(as_human_readable(url))

class CompareDirectories(DirectoryPaneCommand):
	def __call__(self):
		this = self.pane
		panes = this.window.get_panes()
		this_index = panes.index(this)
		other_index = (this_index + 1) % len(panes)
		left = panes[min(this_index, other_index)]
		right = panes[max(this_index, other_index)]
		res_left = self._select_nonexistent_in_other(left, right)
		res_right = self._select_nonexistent_in_other(right, left)
		if res_left == res_right == 0:
			message = 'The directories contain the same file <em>names</em>.' \
			          '<br/>(Did not compare contents, Size or Modified.)'
		else:
			msg_parts = []
			def report(count, l, r):
				if count:
					msg_parts.append(
						'The %s pane contains %d file%s not present on the %s.'
						% (l, count, '' if count == 1 else 's', r)
					)
			report(res_left, 'left', 'right')
			report(res_right, 'right', 'left')
			message = '<br/>'.join(msg_parts)
		show_alert(message)
	def _select_nonexistent_in_other(self, this, other):
		this.clear_selection()
		other_files = set(iterdir(other.get_path()))
		url = this.get_path()
		nonexistent = set(f for f in iterdir(url) if f not in other_files)
		this.select(join(url, f) for f in nonexistent)
		return len(nonexistent)

if PLATFORM == 'Mac':
	class QuickLook(DirectoryPaneCommand):

		aliases = ('Quick Look',)

		def __call__(self):
			files = chosen_files(self)
			if not files:
				return
			if any(not is_file_url(f) for f in files):
				show_alert('Sorry, can only preview normal files.')
				return
			args = ['qlmanage', '-p']
			args.extend(map(as_human_readable, files))
			Popen(args, stdout=DEVNULL, stderr=DEVNULL)
