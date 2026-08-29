"""The clipboard commands: Copy, Cut, Paste and "Copy paths to clipboard".

Copy/Cut only put the files *on* the clipboard - the actual work happens in
Paste, which dispatches to the `copy` or `move` command depending on which of
the two filled it. "Copy paths to clipboard" is the odd one out: it copies
text, not files, so it never takes part in that hand-off.
"""
from fman import clipboard, DirectoryPaneCommand, PLATFORM, show_alert, \
	show_status_message
from fman.fs import exists
from fman.url import as_human_readable

__all__ = [
	'CopyPathsToClipboard', 'CopyToClipboard', 'Cut', 'Paste', 'PasteCut'
]

class CopyPathsToClipboard(DirectoryPaneCommand):
	def __call__(self):
		to_copy = self.get_chosen_files() or [self.pane.get_path()]
		files = '\n'.join(to_copy)
		clipboard.clear()
		clipboard.set_text('\n'.join(map(as_human_readable, to_copy)))
		_report_clipboard_action('Copied', to_copy, ' to the clipboard', 'path')

def _report_clipboard_action(verb, files, suffix='', ftype='file'):
	num = len(files)
	first_file = as_human_readable(files[0])
	if num == 1:
		message = '%s %s%s' % (verb, first_file, suffix)
	else:
		plural = 's' if num > 2 else ''
		message = '%s %s and %d other %s%s%s' % \
				  (verb, first_file, num - 1, ftype, plural, suffix)
	show_status_message(message, timeout_secs=3)

class CopyToClipboard(DirectoryPaneCommand):
	def __call__(self):
		files = self.get_chosen_files()
		if files:
			clipboard.copy_files(files)
			_report_clipboard_action('Copying', files)
		else:
			show_alert(NO_SELECTION)
	def is_visible(self):
		return bool(self.pane.get_file_under_cursor())

class Cut(DirectoryPaneCommand):
	def __call__(self):
		if PLATFORM == 'Mac':
			show_alert(
				"Sorry, macOS doesn't support cutting files. Please press "
				"⌘-C (copy) followed by ⌘-⌥-V (move)."
			)
			return
		files = self.get_chosen_files()
		if files:
			clipboard.cut_files(files)
			_report_clipboard_action('Cutting', files)
		else:
			show_alert(NO_SELECTION)
	def is_visible(self):
		return bool(self.pane.get_file_under_cursor())

class Paste(DirectoryPaneCommand):
	def __call__(self):
		files = clipboard.get_files()
		if not files:
			return
		if clipboard.files_were_cut():
			self.pane.run_command('paste_cut')
		else:
			dest = self.pane.get_path()
			self.pane.run_command('copy', {'files': files, 'dest_dir': dest})
	def is_visible(self):
		return bool(clipboard.get_files())

class PasteCut(DirectoryPaneCommand):
	def __call__(self):
		files = clipboard.get_files()
		if not any(map(exists, files)):
			# This can happen when the paste-cut has already been performed.
			return
		dest_dir = self.pane.get_path()
		self.pane.run_command('move', {
			'files': files,
			'dest_dir': dest_dir
		})
