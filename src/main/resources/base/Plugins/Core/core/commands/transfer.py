"""Moving files somewhere else: copy, move, symlink, drag-and-drop.

All of them ask the same question first - "to where?" - so they share
`_TreeCommand`, which resolves the answer (relative paths, existing
directories, overwriting a single file) before any file is touched.
Packing asks it too, through `get_dest_suggestion` - see
core/commands/pack.py.
"""
# `import *` skips underscore names: get_dest_suggestion splits the extension
# off the name it suggests, the same way the editor's "New file" prompt does.
from core.commands.editor import _find_extension_start
from core.commands.util import get_opposite_pane, is_file_url, \
	CANNOT_READ, NO_SELECTION
from core.fileoperations import CopyFiles, MoveFiles
from core.util import is_parent
from fman import DirectoryPaneCommand, DirectoryPaneListener, NO, YES, \
	YES_TO_ALL, show_alert, submit_task
from fman.fs import makedirs, notify_file_added
from fman.url import as_human_readable, join, splitscheme
# os.path.basename, not fman.url's: this is what core/commands/__init__.py
# used before this module existed (its later `from os.path import basename`
# shadowed the URL one for the whole file).
from os.path import basename
from pathlib import PurePath

import fman
import fman.fs
import os
import re

__all__ = ['Copy', 'DragAndDropListener', 'Move', 'Symlink',
           'get_dest_suggestion']

class _TreeCommand(DirectoryPaneCommand):
	def __call__(self, files=None, dest_dir=None):
		if files is None:
			files = self.get_chosen_files()
			src_dir = self.pane.get_path()
		else:
			# This for instance happens in Drag and Drop operations.
			src_dir = None
		if dest_dir is None:
			dest_dir = get_opposite_pane(self.pane).get_path()
		proceed = self._confirm_tree_operation(files, dest_dir, src_dir)
		if proceed:
			dest_dir, dest_name = proceed
			makedirs(dest_dir, exist_ok=True)
			self._call(files, dest_dir, dest_name)
	def _call(self, files, dest_dir, dest_name=None):
		raise NotImplementedError()
	@classmethod
	def _confirm_tree_operation(
		cls, files, dest_dir, src_dir, ui=fman, fs=fman.fs
	):
		if not files:
			ui.show_alert(NO_SELECTION)
			return
		selection_start = 0
		selection_end = None # Select everything
		if len(files) == 1:
			file_, = files
			dest_name = basename(file_)
			files_descr = '"%s"' % dest_name
			try:
				exists_and_is_dir = fs.is_dir(file_)
			except FileNotFoundError:
				exists_and_is_dir = False
			except OSError as e:
				ui.show_alert(CANNOT_READ % (as_human_readable(file_), e))
				return
			if exists_and_is_dir:
				"""
				There is only one reasonable course of action when the file to
				be copied is a dir: Suggest the parent directory and copy the
				dir into it as a folder. The alternative would be to suggest the
				destination directory and copy the dir's *contents*. But this 
				brings a host of problems: Say we copy folder src/ to (inside) 
				dst/ once, and then a second time. Then src/dst is suggested. It
				already exists. This leads to the remaining logic in this class
				copying to src/dst/dst instead of overwriting the previously 
				copied files.
				
				Another problem with the alternative approach would be that the
				user may copy a folder with a lot of files, and manually type in
				an existing destination directory. If we copied the folder's 
				contents, then the user may end up with thousands of files 
				scattered all over the existing directory when he intended for 
				them to be contained in a separate, single directory.
				
				Finally, the alternative approach might not be able to preserve
				the directory's permissions when an existing destination folder
				is supplied.
				"""
				suggested_dst = as_human_readable(dest_dir)
			else:
				dest_url = join(dest_dir, dest_name)
				suggested_dst, selection_start, selection_end = \
					get_dest_suggestion(dest_url)
		else:
			files_descr = '%d files' % len(files)
			suggested_dst = as_human_readable(dest_dir)
		message = '%s %s to' % (cls._verb().capitalize(), files_descr)
		dest, ok = ui.show_prompt(
			message, suggested_dst, selection_start, selection_end
		)
		if dest and ok:
			dest_url = _from_human_readable(dest, dest_dir, src_dir)
			if fs.exists(dest_url):
				try:
					dest_is_dir = fs.is_dir(dest_url)
				except OSError as e:
					ui.show_alert(CANNOT_READ % (dest, e))
					return
				if dest_is_dir:
					if len(files) == 1 and fs.samefile(dest_url, files[0]):
						# This happens when renaming a/ -> A/ on
						# case-insensitive file systems.
						return _split(dest_url)
					for file_ in files:
						if is_parent(file_, dest_url, fs):
							ui.show_alert(
								'You cannot %s a file to itself!' % cls._verb()
							)
							return
					return dest_url, None
				else:
					if len(files) == 1:
						return _split(dest_url)
					else:
						ui.show_alert(
							'You cannot %s multiple files to a single file!' %
							cls._verb()
						)
			else:
				if len(files) == 1:
					return _split(dest_url)
				else:
					choice = ui.show_alert(
						'%s does not exist. Do you want to create it '
						'as a directory and %s the files there?' %
						(as_human_readable(dest_url), cls._verb()),
						YES | NO, YES
					)
					if choice & YES:
						return dest_url, None
	@classmethod
	def _verb(cls):
		return cls.__name__.lower()
	def is_visible(self):
		return bool(self.pane.get_file_under_cursor())

def get_dest_suggestion(dst_url):
	scheme = splitscheme(dst_url)[0]
	if scheme == 'file://':
		sep = os.sep
		suggested_dst = as_human_readable(dst_url)
		offset = 0
	else:
		sep = '/'
		suggested_dst = dst_url
		offset = len(scheme)
	try:
		last_sep = suggested_dst.rindex(sep, offset)
	except ValueError as no_sep:
		selection_start = offset
	else:
		selection_start = last_sep + 1
	selection_end = _find_extension_start(suggested_dst, selection_start)
	return suggested_dst, selection_start, selection_end

def _from_human_readable(path_or_url, dest_dir, src_dir):
	try:
		splitscheme(path_or_url)
	except ValueError as no_scheme:
		dest_scheme, dest_dir_path = splitscheme(dest_dir)
		if src_dir:
			# Treat dest as relative to src_dir:
			src_scheme, src_path = splitscheme(src_dir)
			dest_path = PurePath(src_path, path_or_url).as_posix()
		else:
			dest_path = PurePath(dest_dir_path, path_or_url).as_posix()
		path_or_url = dest_scheme + dest_path
	return path_or_url

def _split(url):
	scheme, tail = splitscheme(url)
	head, tail = re.match('(/*)(.*?)$', tail).groups()
	if '/' in tail:
		h2, tail = tail.rsplit('/', 1)
		head += h2
	return scheme + head, tail

class Copy(_TreeCommand):
	def _call(self, files, dest_dir, dest_name=None):
		submit_task(CopyFiles(files, dest_dir, dest_name))

class Move(_TreeCommand):
	def _call(self, files, dest_dir, dest_name=None):
		submit_task(MoveFiles(files, dest_dir, dest_name))

class DragAndDropListener(DirectoryPaneListener):
	def on_files_dropped(self, file_urls, dest_dir, is_copy_not_move):
		command = self._get_command(file_urls, dest_dir, is_copy_not_move)
		self.pane.run_command(
			command, {'files': file_urls, 'dest_dir': dest_dir}
		)
	def _get_command(self, file_urls, dest_dir, is_copy_not_move):
		schemes = set(splitscheme(url)[0] for url in file_urls)
		src_scheme = next(iter(schemes)) if len(schemes) == 1 else ''
		dest_scheme = splitscheme(dest_dir)[0]
		if src_scheme != dest_scheme:
			# The default value for `is_copy_not_move` is False. But consider
			# the case where the user drags a file from a Zip archive to the
			# local file system. In this case, `is_copy_not_move` might indicate
			# "move" simply because it's the default. But most likely, the user
			# simply wants to extract the file and not also remove it from the
			# Zip file. Respect this:
			is_copy_not_move = True
		return 'copy' if is_copy_not_move else 'move'

class Symlink(_TreeCommand):

	aliases = ('Symlink',)

	def is_visible(self):
		if not super().is_visible():
			return False
		return is_file_url(self.pane.get_path()) and \
			   is_file_url(get_opposite_pane(self.pane).get_path())

	def __call__(self):
		src_url = self.pane.get_path()
		if not is_file_url(src_url):
			self._refuse()
			return
		dest_url = get_opposite_pane(self.pane).get_path()
		if not is_file_url(dest_url):
			self._refuse()
			return
		super().__call__()

	def _call(self, files, dest_dir, dest_name=None):
		ignore_exists = False
		for i, f_url in enumerate(files):
			dest_url = join(dest_dir, dest_name or basename(f_url))
			if not is_file_url(f_url) or not is_file_url(dest_url):
				self._refuse()
				return
			f_path = as_human_readable(f_url)
			dest_path = as_human_readable(dest_url)
			try:
				os.symlink(f_path, dest_path, is_dir(f_url))
			except FileExistsError:
				if ignore_exists:
					continue
				has_more = i < len(files) - 1
				if has_more:
					answer = show_alert(
						"%s exists and cannot be symlinked. Continue?"
						% basename(f_url),
						YES | NO | YES_TO_ALL, YES
					)
					if answer & YES_TO_ALL:
						ignore_exists = True
					elif answer & NO:
						break
				else:
					show_alert(
						"%s exists and cannot be symlinked." % basename(f_url)
					)
			else:
				notify_file_added(dest_url)

	def _refuse(self):
		show_alert('Sorry, can only create symlinks between local files.')
