"""The OS's own "Properties" / "Get Info" window for the chosen files.

Platform-specific by nature: macOS drives Finder over AppleScript, Windows
calls the shell dialog from core/commands/explorer_properties.py. On Windows
that import can fail (it needs pywin32), so a stand-in command that explains
the failure takes its place - the command name has to keep existing either
way, or key bindings pointing at it get dropped as unknown.
"""
from fman import DirectoryPaneCommand, PLATFORM, links, show_alert
from fman.url import splitscheme
from subprocess import Popen, DEVNULL, PIPE

__all__ = []
if PLATFORM == 'Mac':
	__all__.append('GetInfo')
elif PLATFORM == 'Windows':
	__all__.append('ShowExplorerProperties')

if PLATFORM == 'Mac':
	class GetInfo(DirectoryPaneCommand):
		def __call__(self):
			files = self.get_chosen_files() or [self.pane.get_path()]
			self._run_applescript(
				'on run args\n'
				'	tell app "Finder"\n'
				'		activate\n'
				'		repeat with f in args\n'
				'			open information window of '
							'(posix file (contents of f) as alias)\n'
				'		end\n'
				'	end\n'
				'end\n',
				_get_local_filepaths(files)
			)
		def _run_applescript(self, script, args=None):
			if args is None:
				args = []
			process = Popen(
				['osascript', '-'] + args, stdin=PIPE,
				stdout=DEVNULL, stderr=DEVNULL
			)
			process.communicate(script.encode('ascii'))
elif PLATFORM == 'Windows':
	try:
		from .explorer_properties import ShowExplorerProperties
	except ImportError as e:
		# If we simply refer to `e` below, we get a NameError. This is likely
		# because the captured exception of `except` statements goes out of
		# scope as soon as the except block exits. So introduce a separate
		# variable that does not go out of scope:
		error = e
		class ShowExplorerProperties(DirectoryPaneCommand):
			def __call__(self):
				show_alert(
					'Sorry, the module for displaying file properties %r could '
					'not be loaded. Please file a bug report at '
					'<a href="' + links.ISSUES + '">'
					+ links.ISSUES + '</a> mentioning your Windows '
					'version (eg. Windows 10) and architecture (eg. 64 bit).'
					% error.name
				)

def _get_local_filepaths(urls):
	result = []
	for url in urls:
		scheme, path = splitscheme(url)
		if scheme == 'file://':
			result.append(path)
	return result
