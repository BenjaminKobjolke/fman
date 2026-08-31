"""Deleting files: "Move to trash" and "Delete permanently".

Both commands ask for confirmation and then hand the work to `_Delete`, a
Task that prepares one sub-task per URL before running any of them - so a
filesystem that cannot delete at all fails before the first file is gone.
"Move to trash" falls back to a permanent delete on filesystems that do not
implement `prepare_trash`.
"""
from fman import DirectoryPaneCommand, PLATFORM, show_alert, submit_task, \
	Task, NO, YES, YES_TO_ALL
from fman.fs import prepare_delete, prepare_trash
from core.commands.util import NO_SELECTION
from fman.url import splitscheme
from io import UnsupportedOperation
from os import strerror
from os.path import basename

__all__ = ['DeletePermanently', 'MoveToTrash']

class MoveToTrash(DirectoryPaneCommand):

	aliases = ('Delete',)

	def __call__(self, urls=None):
		if urls is None:
			urls = self.get_chosen_files()
		if not urls:
			show_alert(NO_SELECTION)
			return
		if confirm_trash(urls):
			trash(urls)
	def is_visible(self):
		return bool(self.pane.get_file_under_cursor())

# Split out of MoveToTrash.__call__ so the in-pane viewers can reuse this
# command's wording and machinery without a second confirmation of their own
# (core/viewer_file_ops.py). Two functions rather than one because the viewer
# has to confirm first, move its cursor off the doomed file and only then
# submit - _Delete runs in the background, so a delete submitted before the
# cursor moves races the pane model. Deliberately not in __all__, which is what
# keeps them from being picked up as commands.
def confirm_trash(urls):
	description = _describe(urls, 'these %d files')
	trash_name = 'Recycle Bin' if PLATFORM == 'Windows' else 'Trash'
	msg = \
		"Do you really want to move %s to the %s?" % (description, trash_name)
	return bool(show_alert(msg, YES | NO, YES) & YES)

def trash(urls):
	submit_task(_Delete(urls, prepare_trash, prepare_delete))

class DeletePermanently(DirectoryPaneCommand):
	def __call__(self, urls=None):
		if urls is None:
			urls = self.get_chosen_files()
		if not urls:
			show_alert(NO_SELECTION)
			return
		description = _describe(urls, 'these %d items')
		message = \
			"Do you really want to PERMANENTLY delete %s? This action cannot " \
			"be undone!" % description
		if show_alert(message, YES | NO, YES) & YES:
			submit_task(_Delete(urls, prepare_delete))

class _Delete(Task):
	def __init__(self, urls, prepare_fn, fallback=None):
		super().__init__('Deleting ' + _describe(urls))
		self._urls = urls
		self._num_urls_prepared = 0
		self._prepare_fn = prepare_fn
		self._fallback = fallback
		self._tasks = []
	def __call__(self):
		try:
			self._gather_tasks()
		except (UnsupportedOperation, NotImplementedError):
			failing_url = self._urls[self._num_urls_prepared]
			self.show_alert(
				'Deleting files in %s is not supported.'
				% splitscheme(failing_url)[0]
			)
			return
		ignore_errors = False
		for i, task in enumerate(self._tasks):
			self.check_canceled()
			try:
				self.run(task)
			except FileNotFoundError:
				# Perhaps the file has already been deleted.
				pass
			except OSError as e:
				if ignore_errors:
					continue
				text = task.get_title()
				message = 'Error ' + text[0].lower() + text[1:]
				reason = e.strerror or ''
				if not reason and e.errno is not None:
					reason = strerror(e.errno)
				if reason:
					message += ': ' + reason
				message += '.'
				is_last = i == len(self._tasks) - 1
				if is_last:
					self.show_alert(message)
				else:
					message += ' Do you want to continue?'
					choice = show_alert(message, YES | NO | YES_TO_ALL)
					if choice & NO:
						break
					if choice & YES_TO_ALL:
						ignore_errors = True
	def _gather_tasks(self):
		for url in self._urls:
			try:
				self._prepare(url, self._prepare_fn)
			except (NotImplementedError, UnsupportedOperation):
				if self._fallback is None:
					raise
				self._prepare(url, self._fallback)
			self._num_urls_prepared += 1
		self.set_size(sum(t.get_size() for t in self._tasks))
	def _prepare(self, url, prepare_fn):
		url_tasks = []
		for task in prepare_fn(url):
			self.check_canceled()
			url_tasks.append(task)
			if task.get_size():
				num = len(self._tasks) + len(url_tasks)
				self.set_text('Preparing to delete {:,} files.'.format(num))
		self._tasks.extend(url_tasks)

def _describe(files, template='%d files'):
	if len(files) == 1:
		return basename(files[0])
	return template % len(files)
