from core.commands.util import get_opposite_pane, is_file_url
from core.fileoperations import CopyFiles, MoveFiles
from core.github import find_repos, GitHubRepo
from core.os_ import open_terminal_in_directory, open_native_file_manager, \
	get_popen_kwargs_for_opening
from core.util import listdir_absolute, is_parent
from core.quicksearch_screen import QuicksearchScreen
from core.quicksearch_matchers import contains_chars
from core.viewers import viewer_for
from fman import *
from fman.fs import exists, mkdir, is_dir, delete, copy, iterdir, \
	resolve, prepare_copy, makedirs, notify_file_added
from fman import links
from fman.impl.util import get_user
from fman.url import splitscheme, as_url, join, basename, \
	as_human_readable, dirname
from os.path import basename
from pathlib import PurePath
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
from subprocess import Popen, DEVNULL, PIPE
from tempfile import TemporaryDirectory
from urllib.error import URLError

import errno
import fman.fs
import json
import os
import os.path
import re
import sys

from .archives import *
# `import *` skips underscore names, and Pack needs the same suffix -> scheme
# lookup to decide which filesystem should create the archive it packs into.
from .archives import _get_handler_for_archive
from .clipboard import *
from .columns import *
from .deletion import *
# `import *` skips underscore names, but Pack's task title reuses the same
# "1 file / N files" phrasing as the delete tasks.
from .deletion import _describe
from .editor import *
# `import *` skips underscore names, and code still in this file needs
# three of them: get_dest_suggestion splits the extension off a rename
# suggestion, and OpenWith's app dialogs reuse the editor picker.
from .editor import _find_extension_start, _PLATFORM_APPLICATIONS_FILTER, \
	_show_app_open_dialog
from .goto import *
from .hidden_files import *
from .palette import *
from .pane_view import *
from .places import *
from .release_notes import *
from .rename import *
from .theme import *
from .window import *

class About(ApplicationCommand):
	def __call__(self):
		show_alert("fman version: " + FMAN_VERSION)

class Help(ApplicationCommand):

	aliases = ('Help',)

	def __call__(self):
		QDesktopServices.openUrl(QUrl(links.HELP))

class MoveCursorDown(DirectoryPaneCommand):
	def __call__(self, toggle_selection=False):
		self.pane.move_cursor_down(toggle_selection)

class MoveCursorUp(DirectoryPaneCommand):
	def __call__(self, toggle_selection=False):
		self.pane.move_cursor_up(toggle_selection)

class MoveCursorHome(DirectoryPaneCommand):
	def __call__(self, toggle_selection=False):
		self.pane.move_cursor_home(toggle_selection)

class MoveCursorEnd(DirectoryPaneCommand):
	def __call__(self, toggle_selection=False):
		self.pane.move_cursor_end(toggle_selection)

class MoveCursorPageUp(DirectoryPaneCommand):
	def __call__(self, toggle_selection=False):
		self.pane.move_cursor_page_up(toggle_selection)

class MoveCursorPageDown(DirectoryPaneCommand):
	def __call__(self, toggle_selection=False):
		self.pane.move_cursor_page_down(toggle_selection)

class ToggleSelection(DirectoryPaneCommand):
	def __call__(self):
		file_under_cursor = self.pane.get_file_under_cursor()
		if file_under_cursor:
			self.pane.toggle_selection(file_under_cursor)

class GoUp(DirectoryPaneCommand):

	aliases = ('Go up',)

	def __call__(self):
		go_up(self.pane)

def go_up(pane):
	path_before = pane.get_path()
	def callback():
		path_now = pane.get_path()
		# Only move the cursor if we actually changed directories; For
		# instance, we don't want to move the cursor if the user presses
		# Backspace while at drives:// and the cursor is already at
		# drives://C:
		if path_now != path_before:
			# Consider: The user is in zip:///Temp.zip and invokes GoUp.
			# This takes us to file:///. We want to place the cursor at
			# file:///Temp.zip. "Switch" schemes to make this happen:
			cursor_dest = splitscheme(path_now)[0] + \
						  splitscheme(path_before)[1]
			try:
				pane.place_cursor_at(cursor_dest)
			except ValueError as dest_doesnt_exist:
				pane.move_cursor_home()
	parent_dir = dirname(path_before)
	try:
		pane.set_path(parent_dir, callback)
	except FileNotFoundError:
		# This for instance happens when the user pressed backspace when at
		# file:/// on Unix.
		pass

class Open(DirectoryPaneCommand):
	def __call__(self, url=None):
		if url is None:
			url = self.pane.get_file_under_cursor()
		if url:
			try:
				url_is_dir = is_dir(url)
			except OSError as e:
				show_alert(
					'Could not read from %s (%s)' % (as_human_readable(url), e)
				)
				return
			# Use `run_command` to delegate the actual opening. This makes it
			# possible for plugins to modify the default open behaviour by
			# implementing DirectoryPaneListener#on_command(...).
			if url_is_dir:
				if PLATFORM == 'Mac' and url.endswith('.app'):
					dialogs = load_json('Core Dialogs.json', default={})
					if not dialogs.get('open_app_hint_shown', False):
						show_alert(
							'Quick tip: Apps in macOS are directories. When '
							'you press '
							'<span style="color: white;">Enter</span>, '
							'fman therefore browses them. If you want to '
							'launch the app instead, press '
							'<span style="color: white;">Cmd+Enter</span>.'
						)
						dialogs['open_app_hint_shown'] = True
						save_json('Core Dialogs.json')
						return
				self.pane.run_command('open_directory', {'url': url})
			else:
				self.pane.run_command('open_file', {'url': url})
		else:
			show_alert('No file is selected!')

class OpenListener(DirectoryPaneListener):
	def on_doubleclicked(self, file_url):
		self.pane.run_command('open', {'url': file_url})

class OpenDirectory(DirectoryPaneCommand):
	def __call__(self, url):
		try:
			url_is_dir = is_dir(url)
		except OSError as e:
			show_alert(
				'Could not read from %s (%s)' % (as_human_readable(url), e)
			)
			return
		if url_is_dir:
			try:
				self.pane.set_path(url, onerror=None)
			except PermissionError:
				show_alert(
					'Access to "%s" was denied.' % as_human_readable(url)
				)
		else:
			def callback():
				try:
					self.pane.place_cursor_at(url)
				except ValueError as file_disappeared:
					pass
			self.pane.set_path(dirname(url), callback=callback, onerror=None)
	def is_visible(self):
		return False

class OpenFile(DirectoryPaneCommand):
	def __call__(self, url):
		_open_files([url], self.pane)
	def is_visible(self):
		return False

def _open_files(urls, pane):
	local_file_paths = []
	for url in urls:
		# On Windows, CMD can handle mapped drives Z:\ but not UNC paths
		# //192.168.0.2. If the former maps to the latter, then CMD fails to
		# run .bat files in that location. So only resolve if absolutely
		# necessary, i.e. when not a file:// URL:
		if not is_file_url(url):
			try:
				url = resolve(url)
			except FileNotFoundError:
				# No sense to try to open a file that does not exist.
				continue
			except OSError as e:
				# Not all OSErrors need prevent us from opening the file.
				# So only skip this file if it does not exist:
				if e.errno == errno.ENOENT:
					continue
		scheme = splitscheme(url)[0]
		if scheme != 'file://':
			show_alert(
				'Opening files from %s is not supported. If you are a plugin '
				'developer, you can implement this with '
				'DirectoryPaneListener#on_command(...).' % scheme
			)
			return
		# Use as_human_readable(...) instead of the result from splitscheme(...)
		# above to get backslashes on Windows:
		local_file_paths.append(as_human_readable(url))
	_open_local_files(local_file_paths, pane)

def _open_local_files(paths, pane):
	if PLATFORM == 'Windows':
		_open_local_files_win(paths, pane)
	elif PLATFORM == 'Mac':
		_open_local_files_mac(paths)
	else:
		assert PLATFORM == 'Linux'
		_open_local_files_linux(paths)

def _open_local_files_win(paths, pane):
	# Whichever implementation is used here, it should support:
	#  * C:\picture.jpg
	#  * C:\notepad.exe
	#  * C:\a & b.txt
	#  * C:\batch.bat should print the current dir:
	#        echo %cd%
	#        pause
	#  * \\server\share\picture.jpg
	#  * D:\Book.pdf
	#  * \\cryptomator-vault\app.exe
	for path in paths:
		if path.endswith('.lnk'):
			import win32com.client
			shell = win32com.client.Dispatch("WScript.Shell")
			shortcut = shell.CreateShortCut(path)
			target_url = as_url(shortcut.TargetPath)
			if is_dir(target_url):
				pane.set_path(target_url)
				return
		try:
			from win32api import ShellExecute
			from win32con import SW_SHOWNORMAL
			cwd = os.path.dirname(path)
			ShellExecute(0, None, path, None, cwd, SW_SHOWNORMAL)
		except OSError:
			# This for instance happens when the file is an .exe that requires
			# Admin privileges, but the user cancels the UAC "do you want to run
			# this file?" dialog.
			pass

def _open_local_files_mac(paths):
	non_executables = []
	for path in paths:
		try:
			_run_executable(path)
		except (OSError, ValueError):
			non_executables.append(path)
	if non_executables:
		try:
			Popen(['open'] + non_executables, **_quiet)
		except OSError:
			pass

def _open_local_files_linux(paths):
	for path in paths:
		try:
			_run_executable(path)
		except (OSError, ValueError):
			try:
				Popen(['xdg-open', path], **_quiet)
			except Exception as e:
				raise e from None

def _run_executable(path):
	Popen([path], cwd=os.path.dirname(path), **_quiet)

_quiet = {'stdout': DEVNULL, 'stderr': DEVNULL}

class OpenSelectedFiles(DirectoryPaneCommand):
	def __call__(self):
		file_under_cursor = self.pane.get_file_under_cursor()
		selected_files = self.pane.get_selected_files()
		if file_under_cursor in selected_files:
			_open_files(selected_files, self.pane)
		else:
			_open_files([file_under_cursor], self.pane)
	def is_visible(self):
		return bool(self.get_chosen_files())

def _is_viewable(url):
	# Whether any registered viewer handles url's content - the built-in
	# image/video/text ones (core/viewers.py) plus whatever plugins added.
	return viewer_for(url) is not None

def _view_file_in(source_pane, target_pane, focus_view=True):
	# Read the file under source_pane's cursor and mount the matching viewer
	# into target_pane. focus_view is forwarded to the viewer so it can be
	# mounted without grabbing keyboard focus (see ViewFileInOtherPane).
	url = source_pane.get_file_under_cursor()
	if not url:
		show_alert('No file is selected!')
		return
	if is_dir(url):
		show_alert('Cannot view a directory.')
		return
	if splitscheme(url)[0] != 'file://':
		show_alert('Can only view local files.')
		return
	viewer = viewer_for(url)
	if viewer is None:
		show_alert(
			"Can't view this file here — it looks binary. Press Enter "
			'or use Open to launch it with the default app.'
		)
		return
	viewer.show(target_pane, url, focus_view=focus_view)

class ViewFile(DirectoryPaneCommand):

	# Palette-only by design, like ResetPaneFontSize — no default key
	# binding, so it doesn't change Enter/double-click behaviour.
	aliases = ('View file',)

	def __call__(self):
		_view_file_in(self.pane, self.pane)

class ViewFileInOtherPane(DirectoryPaneCommand):

	# Like ViewFile, but mounts the viewer in the *other* pane so this pane's
	# file list stays visible. Keyboard focus deliberately stays here, so you
	# can keep browsing files while each one previews in the other pane. With
	# only one pane open, target is this pane, so the viewer takes focus as
	# usual. Palette-only by default (no key binding).
	aliases = ('View file in other pane',)

	def __call__(self):
		target = get_opposite_pane(self.pane)
		_view_file_in(self.pane, target, focus_view=target is self.pane)

class OpenOrView(DirectoryPaneCommand):

	# Folder -> navigate in (like Open); viewable file -> internal viewer
	# (like ViewFile); anything the viewer can't handle (binary, non-local)
	# -> OS-open, same as before the viewer existed. Bind to Enter to make
	# the viewer the default file action without losing folder navigation or
	# garbling binaries.
	aliases = ('Open or view',)

	def __call__(self):
		url = self.pane.get_file_under_cursor()
		if (url and not is_dir(url) and splitscheme(url)[0] == 'file://'
				and _is_viewable(url)):
			self.pane.run_command('view_file')
		else:
			self.pane.run_command('open')

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
			ui.show_alert('No file is selected!')
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
				ui.show_alert(
					'Could not read from %s (%s)' %
					(as_human_readable(file_), e)
				)
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
					ui.show_alert('Could not read from %s (%s)' % (dest, e))
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

class SelectAll(DirectoryPaneCommand):
	def __call__(self):
		self.pane.select_all()

class Deselect(DirectoryPaneCommand):
	def __call__(self):
		self.pane.clear_selection()

class InvertSelection(DirectoryPaneCommand):
	def __call__(self, *args, **kwargs):
		url = self.pane.get_path()
		all_files = (join(url, fname) for fname in iterdir(url))
		to_deselect = set(self.pane.get_selected_files())
		to_select = (f for f in all_files if f not in to_deselect)
		self.pane.deselect(to_deselect)
		self.pane.select(to_select)

class _OpenInPaneCommand(DirectoryPaneCommand):
	def __call__(self):
		panes = self.pane.window.get_panes()
		num_panes = len(panes)
		if num_panes < 2:
			raise NotImplementedError()
		this_pane = panes.index(self.pane)
		source_pane = panes[self.get_source_pane(this_pane, num_panes)]
		if source_pane is self.pane:
			to_open = source_pane.get_file_under_cursor() or \
					  source_pane.get_path()
		else:
			# This for instance happens when the right pane is active and the
			# user asks to "open in the right pane". The source pane in this
			# case is the left pane. The cursor in the left pane is not visible
			# (because the right pane is active) - but it still exists and might
			# be over a directory! If we opened the directory under the cursor,
			# we would thus open a subdirectory of the left pane. That's not
			# what we want. We want to open the directory of the left pane:
			to_open = source_pane.get_path()
		dest_pane = panes[self.get_destination_pane(this_pane, num_panes)]
		dest_pane.run_command('open_directory', {'url': to_open})
	def get_source_pane(self, this_pane, num_panes):
		raise NotImplementedError()
	def get_destination_pane(self, this_pane, num_panes):
		raise NotImplementedError()

class OpenInRightPane(_OpenInPaneCommand):
	def get_source_pane(self, this_pane, num_panes):
		if this_pane == num_panes - 1:
			return this_pane - 1
		return this_pane
	def get_destination_pane(self, this_pane, num_panes):
		return min(this_pane + 1, num_panes - 1)

class OpenInLeftPane(_OpenInPaneCommand):
	def get_source_pane(self, this_pane, num_panes):
		if this_pane > 0:
			return this_pane
		return 1
	def get_destination_pane(self, this_pane, num_panes):
		return max(this_pane - 1, 0)

class ShowVolumes(DirectoryPaneCommand):

	aliases = ('Show volumes',)

	def __call__(self, pane_index=None):
		if pane_index is None:
			pane = self.pane
		else:
			pane = self.pane.window.get_panes()[pane_index]
		def callback():
			pane.focus()
			pane.move_cursor_home()
		pane.set_path(_get_volumes_url(), callback=callback)

def _get_volumes_url():
	if PLATFORM == 'Mac':
		return 'file:///Volumes'
	elif PLATFORM == 'Windows':
		return 'drives://'
	elif PLATFORM == 'Linux':
		if os.path.isdir('/media'):
			contents = os.listdir('/media')
			user_name = get_user()
			if contents == [user_name]:
				return as_url(os.path.join('/media', user_name))
			else:
				return 'file:///media'
		else:
			return 'file:///mnt'
	else:
		raise NotImplementedError(PLATFORM)

class DoNothing(DirectoryPaneCommand):

	"""
	Exists only to be bound to: unbinding a shipped default means shadowing it
	with a higher-priority binding, and fman's sanitizer drops bindings whose
	command doesn't exist. See core/binding_editor.py.
	"""

	aliases = ('Do nothing',)

	def __call__(self):
		pass
	def is_visible(self):
		# Nothing to run from the palette - it is a target, not an action.
		return False

class Quit(ApplicationCommand):

	aliases = ('Quit',)

	def __call__(self):
		sys.exit(0)

class ZenOfFman(ApplicationCommand):
	def __call__(self):
		show_alert(
			"The Zen of fman\n"
			+ links.ZEN + "\n\n"
			"Looks matter\n"
			"Speed counts\n"
			"Extending must be easy\n"
			"Customisability is important\n"
			"But not at the expense of speed\n"
			"I/O is better asynchronous\n"
			"Updates should be transparent and continuous\n"
			"Don't reinvent the wheel"
		)

class OpenDataDirectory(DirectoryPaneCommand):
	def __call__(self):
		self.pane.set_path(as_url(DATA_DIRECTORY))

class GoBack(DirectoryPaneCommand):
	def __call__(self):
		HistoryListener.INSTANCES[self.pane].go_back()

class GoForward(DirectoryPaneCommand):
	def __call__(self):
		HistoryListener.INSTANCES[self.pane].go_forward()

class HistoryListener(DirectoryPaneListener):

	INSTANCES = {}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._history = History()
		self.INSTANCES[self.pane] = self
	def go_back(self):
		try:
			path = self._history.go_back()
		except ValueError:
			return
		self._navigate_to(path)
	def go_forward(self):
		try:
			path = self._history.go_forward()
		except ValueError:
			return
		self._navigate_to(path)
	def _navigate_to(self, path):
		if path == dirname(self.pane.get_path()):
			# Place the cursor at the current directory after going up:
			go_up(self.pane)
		else:
			self.pane.set_path(path)
	def on_path_changed(self):
		self._history.path_changed(self.pane.get_path())

class History:
	def __init__(self):
		self._paths = []
		self._curr_path = -1
		self._ignore_next_path_change = False
	def go_back(self):
		if self._curr_path <= 0:
			raise ValueError()
		self._curr_path -= 1
		self._ignore_next_path_change = True
		return self._paths[self._curr_path]
	def go_forward(self):
		if self._curr_path >= len(self._paths) - 1:
			raise ValueError()
		self._curr_path += 1
		self._ignore_next_path_change = True
		return self._paths[self._curr_path]
	def path_changed(self, path):
		if path == 'null://':
			return
		if self._ignore_next_path_change:
			self._ignore_next_path_change = False
			return
		self._curr_path += 1
		del self._paths[self._curr_path:]
		self._paths.append(path)

class InstallPlugin(ApplicationCommand):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._plugin_repos = None
	def __call__(self, github_repo=None):
		if github_repo:
			with StatusMessage('Fetching GitHub repo %s...' % github_repo):
				repo = GitHubRepo.fetch(github_repo)
		else:
			if self._plugin_repos is None:
				with StatusMessage('Fetching available plugins...'):
					try:
						self._plugin_repos = \
							find_repos(topics=['fman', 'plugin'])
					except URLError as e:
						show_alert(
							'Could not fetch available plugins: %s.' % e.reason
						)
						return
			result = show_quicksearch(self._get_matching_repos)
			repo = result[1] if result else None
		if repo:
			with StatusMessage('Downloading %s...' % repo.name):
				try:
					ref = repo.get_latest_release()
				except LookupError as no_release_yet:
					ref = repo.get_latest_commit()
				zipball_contents = repo.download_zipball(ref)
			plugin_dir = self._install_plugin(repo.name, zipball_contents)
			# Save some data in case we want to update the plugin later:
			self._record_plugin_installation(plugin_dir, repo.url, ref)
			success = self._load_installed_plugin(plugin_dir)
			if success:
				show_alert('Plugin %r was successfully installed.' % repo.name)
	def _get_matching_repos(self, query):
		installed_plugins = set(
			os.path.basename(plugin_dir)
			for plugin_dir in _get_thirdparty_plugins()
		)
		for repo in self._plugin_repos:
			if repo.name in installed_plugins:
				continue
			match = contains_chars(repo.name.lower(), query.lower())
			if match or not query:
				hint = '%d ★' % repo.num_stars if repo.num_stars else ''
				yield QuicksearchItem(
					repo, repo.name, match, hint=hint,
					description=repo.description
				)
	def _install_plugin(self, name, zipball_contents):
		os.makedirs(_THIRDPARTY_PLUGINS_DIR, exist_ok=True)
		dest_dir = os.path.join(_THIRDPARTY_PLUGINS_DIR, name)
		dest_dir_url = as_url(dest_dir)
		if exists(dest_dir_url):
			raise ValueError('Plugin %s seems to already be installed.' % name)
		# We purposely don't use Python's ZipFile here because it does not
		# preserve the executable bit of extracted files. This would present a
		# problem for plugins shipping with their own binaries.
		with TemporaryDirectory() as tmp_dir:
			zip_path = os.path.join(tmp_dir, 'plugin.zip')
			with open(zip_path, 'wb') as f:
				f.write(zipball_contents)
			zip_url = as_url(zip_path, 'zip://')
			dir_in_zip, = iterdir(zip_url)
			copy(join(zip_url, dir_in_zip), dest_dir_url)
		return dest_dir
	def _load_installed_plugin(self, plugin_dir):
		# Unload plugins later than the given plugin in the load order, load
		# the plugin, then load the unloaded plugins again. This inserts the
		# given plugin in the correct place in the load order.
		plugins = _get_plugins()
		plugin_index = plugins.index(plugin_dir)
		to_unload = plugins[plugin_index + 1:]
		with PreservePanePaths(self.window):
			for plugin in reversed(to_unload):
				try:
					unload_plugin(plugin)
				except ValueError as was_not_loaded:
					pass
			result = load_plugin(plugin_dir)
			for plugin in to_unload:
				load_plugin(plugin)
		return result
	def _record_plugin_installation(self, plugin_dir, repo_url, ref):
		plugin_json = os.path.join(plugin_dir, 'Plugin.json')
		if os.path.exists(plugin_json):
			with open(plugin_json, 'r') as f:
				data = json.load(f)
		else:
			data = {}
		data['url'] = repo_url
		data['ref'] = ref
		with open(plugin_json, 'w') as f:
			json.dump(data, f)

_THIRDPARTY_PLUGINS_DIR = os.path.join(DATA_DIRECTORY, 'Plugins', 'Third-party')

def _get_thirdparty_plugins():
	return _list_plugins(_THIRDPARTY_PLUGINS_DIR)

def _list_plugins(dir_path):
	try:
		return list(filter(os.path.isdir, listdir_absolute(dir_path)))
	except FileNotFoundError:
		return []

class RemovePlugin(ApplicationCommand):

	aliases = ('Remove plugin',)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._installed_plugins = None
	def __call__(self):
		self._installed_plugins = _get_thirdparty_plugins()
		if not self._installed_plugins:
			show_alert("You don't seem to have any plugins installed.")
		else:
			result = show_quicksearch(self._get_matching_plugins)
			if result:
				plugin_dir = result[1]
				if plugin_dir:
					try:
						unload_plugin(plugin_dir)
					except ValueError as plugin_was_not_loaded:
						pass
					delete(as_url(plugin_dir))
					show_alert(
						'Plugin %r was successfully removed.'
						% os.path.basename(plugin_dir)
					)
	def _get_matching_plugins(self, query):
		for plugin_dir in self._installed_plugins:
			plugin_name = os.path.basename(plugin_dir)
			match = contains_chars(plugin_name.lower(), query.lower())
			if match or not query:
				yield QuicksearchItem(plugin_dir, plugin_name, highlight=match)

class ReloadPlugins(ApplicationCommand):
	def __call__(self):
		plugins = _get_plugins()
		with PreservePanePaths(self.window):
			for plugin in reversed(plugins):
				try:
					unload_plugin(plugin)
				except ValueError as plugin_had_not_been_loaded:
					pass
			for plugin in plugins:
				load_plugin(plugin)
		num_plugins = len(plugins)
		plural = 's' if num_plugins > 1 else ''
		show_status_message(
			'Reloaded %d plugin%s.' % (num_plugins, plural), timeout_secs=2
		)

class PreservePanePaths:
	# When a pane is currently displaying a location with a file system that
	# is "reloaded", its location gets lost. So save the locations and
	# restore them later.
	def __init__(self, window):
		self._window = window
		self._paths_before = []
	def __enter__(self):
		self._paths_before = \
			[pane.get_path() for pane in (self._window.get_panes())]
		return self
	def __exit__(self, exc_type, exc_val, exc_tb):
		for pane, path in zip(self._window.get_panes(), self._paths_before):
			pane.set_path(path)

def _get_plugins():
	return _get_thirdparty_plugins() + _get_user_plugins()

def _get_user_plugins():
	result = []
	settings_plugin = ''
	user_plugins_dir = os.path.join(DATA_DIRECTORY, 'Plugins', 'User')
	for plugin_dir in _list_plugins(user_plugins_dir):
		if os.path.basename(plugin_dir) == 'Settings':
			settings_plugin = plugin_dir
		else:
			result.append(plugin_dir)
	# According to the fman docs, the Settings plugin is loaded last:
	if settings_plugin:
		result.append(settings_plugin)
	return result

class ListPlugins(DirectoryPaneCommand):
	def __call__(self):
		result = show_quicksearch(self._get_matching_plugins)
		if result:
			plugin_dir = result[1]
			if plugin_dir:
				self.pane.set_path(as_url(plugin_dir), onerror=None)
	def _get_matching_plugins(self, query):
		result = []
		for plugin_dir in _get_thirdparty_plugins():
			plugin_name = os.path.basename(plugin_dir)
			match = contains_chars(plugin_name.lower(), query.lower())
			if match or not query:
				plugin_json = os.path.join(plugin_dir, 'Plugin.json')
				try:
					with open(plugin_json, 'r') as f:
						ref = json.load(f).get('ref', '')
				except OSError:
					ref = ''
				is_sha = len(ref) == 40
				if is_sha:
					ref = ref[:8]
				result.append(QuicksearchItem(
					plugin_dir, plugin_name, highlight=match, hint=ref
				))
		for plugin_dir in _get_user_plugins():
			plugin_name = os.path.basename(plugin_dir)
			match = contains_chars(plugin_name.lower(), query.lower())
			if match or not query:
				result.append(
					QuicksearchItem(plugin_dir, plugin_name, highlight=match)
				)
		return sorted(result, key=lambda qsi: qsi.title)

class StatusMessage:
	def __init__(self, message):
		self._message = message
	def __enter__(self):
		show_status_message(self._message)
	def __exit__(self, *_):
		clear_status_message()

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

class Pack(DirectoryPaneCommand):

	aliases = ('Pack to archive (.zip, .7z, .tar)',)

	def __call__(self):
		files = self.get_chosen_files()
		if not files:
			show_alert('No file is selected!')
			return
		if len(files) == 1:
			dest_name = PurePath(basename(files[0])).stem + '.zip'
		else:
			dest_name = basename(self.pane.get_path()) + '.zip'
		dest_dir = get_opposite_pane(self.pane).get_path()
		dest_url = join(dest_dir, dest_name)
		suggested_dst, selection_start, selection_end = \
			get_dest_suggestion(dest_url)
		dest, ok = show_prompt(
			'Pack %s to (.zip, .7z, .tar):' % _describe(files), suggested_dst,
			selection_start, selection_end
		)
		if dest and ok:
			dest = _from_human_readable(dest, dest_dir, self.pane.get_path())
			scheme = _get_handler_for_archive(basename(dest))
			if not scheme:
				show_alert('Sorry, but this archive format is not supported.')
				return
			dest_rewritten = scheme + splitscheme(dest)[1]
			try:
				# Create empty archive:
				mkdir(dest_rewritten)
			except FileExistsError:
				answer = show_alert(
					'%s already exists. Do you want to add/update the selected '
					'files?' % basename(dest_rewritten), YES | NO, YES
				)
				if not answer & YES:
					return
			submit_task(_Pack(files, dest_rewritten))
	def is_visible(self):
		return bool(self.pane.get_file_under_cursor())

class _Pack(Task):
	def __init__(self, files, archive_url):
		super().__init__('Packing ' + _describe(files), size=len(files) * 100)
		self._files = files
		self._archive = archive_url
	def __call__(self):
		for f in self._files:
			for task in prepare_copy(f, join(self._archive, basename(f))):
				self.check_canceled()
				self.run(task)

class OpenWith(DirectoryPaneCommand):

	aliases = 'Open with...',

	_OTHER = 'Other...'

	def __call__(self, app=None):
		files, error_msg = self._get_chosen_files()
		if error_msg:
			show_alert(error_msg)
			return
		is_first_execution = not _load_apps()
		if is_first_execution:
			app = _add_app()
			if app:
				_open_files_with_app(files, app)
		else:
			if app is None:
				ShowAppsForOpening(files).show()
			else:
				_open_files_with_app(files, app)
	def _get_chosen_files(self):
		urls = self.get_chosen_files()
		if not urls:
			return [], 'No file is selected!'
		files = []
		for url in urls:
			try:
				url_resolved = resolve(url)
			except OSError:
				pass
			else:
				scheme, path = splitscheme(url_resolved)
				if scheme != 'file://':
					return \
						[], 'Sorry, opening %s files is not supported.' % scheme
				files.append(as_human_readable(url_resolved))
		return files, ''
	def is_visible(self):
		pane = self.pane
		return is_file_url(pane.get_path()) and pane.get_file_under_cursor()

def _open_files_with_app(files, app):
	associations = _load_file_associations()
	for file_path in files:
		file_name = os.path.basename(file_path)
		try:
			extension = file_name[file_name.rindex('.'):]
		except ValueError:
			extension = ''
		ext_assocs = associations.setdefault(extension, {})
		ext_assocs[app] = ext_assocs.get(app, 0) + 1
	_save_file_associations()
	apps = _load_apps()
	try:
		app_path = apps[app]
	except KeyError:
		# We don't expect this to happen. But JSON files are always susceptible
		# by becoming corrupted, eg. when the user edits them.
		show_alert('Could not find the configuration for %s.' % app)
		return
	Popen(**get_popen_kwargs_for_opening(files, with_=app_path))

def _load_file_associations():
	return load_json('File Associations.json', {})

def _save_file_associations():
	save_json('File Associations.json')

def _load_apps():
	return load_json('Apps.json', {})

def _save_apps():
	save_json('Apps.json')

def _add_app():
	app_path = _show_app_open_dialog('Pick an application')
	if not app_path:
		return
	app_name = os.path.basename(app_path).split('.')[0].capitalize()
	app_name, ok = show_prompt(
		'Please enter a name for the application:', app_name
	)
	if not ok or not app_name:
		return
	apps = _load_apps()
	apps[app_name] = app_path
	_save_apps()
	return app_name

def _remove_app(app):
	apps = _load_apps()
	try:
		del apps[app]
	except KeyError:
		# We don't expect this to happen. But JSON files are always susceptible
		# by becoming corrupted, eg. when the user edits them.
		pass
	_save_apps()
	associations = _load_file_associations()
	for suffix, apps in list(associations.items()):
		apps.pop(app, None)
		if not apps:
			del associations[suffix]
	_save_file_associations()

class ShowAppsForOpening(QuicksearchScreen):

	_CONFIGURE = 'Configure...'

	def __init__(self, files):
		super().__init__()
		self._files = files
	def get_options(self):
		file_associations = sorted(
			_load_file_associations().items(),
			key=lambda tpl: len(tpl[0]), reverse=True
		)
		already_yielded = set()
		for file_path in self._files:
			fname = os.path.basename(file_path)
			for suffix, associations in file_associations:
				if fname.endswith(suffix) and (suffix or '.' not in fname):
					for app, count in sorted(
						associations.items(), key=lambda tpl: tpl[1],
						reverse=True
					):
						if app not in already_yielded:
							yield app
							already_yielded.add(app)
		for app in sorted(_load_apps()):
			if app not in already_yielded:
				yield app
		yield self._CONFIGURE
	def on_selected(self, option):
		if option == self._CONFIGURE:
			Configure(self._files).show()
		else:
			_open_files_with_app(self._files, option)

class Configure(QuicksearchScreen):

	_ADD_APP = 'Add app...'
	_EDIT_APP = 'Edit app...'
	_REMOVE_APP = 'Remove app...'

	def __init__(self, files):
		super().__init__()
		self._files = files
	def get_options(self):
		yield self._ADD_APP
		yield self._EDIT_APP
		yield self._REMOVE_APP
	def on_selected(self, option):
		if option == self._ADD_APP:
			app = _add_app()
			if app:
				_open_files_with_app(self._files, app)
		elif option == self._EDIT_APP:
			EditApp(self._files).show()
		elif option == self._REMOVE_APP:
			RemoveApp(self._files).show()
	def on_cancelled(self):
		ShowAppsForOpening(self._files).show()

class EditApp(QuicksearchScreen):
	def __init__(self, files):
		super().__init__()
		self._files = files
	def get_options(self):
		yield from sorted(_load_apps())
	def on_selected(self, app):
		new_name, ok = \
			show_prompt('Enter the new name for the application:', app)
		if not ok or not new_name:
			Configure(self._files).show()
			return
		apps = _load_apps()
		app_path = apps[app]
		new_path = show_file_open_dialog(
			"Pick an executable", app_path,
			_PLATFORM_APPLICATIONS_FILTER[PLATFORM]
		)
		if not new_path:
			Configure(self._files).show()
			return
		del apps[app]
		apps[new_name] = new_path
		_save_apps()
		associations = _load_file_associations()
		for suffix, app_counts_for_suffix in associations.items():
			try:
				app_counts_for_suffix[new_name] = app_counts_for_suffix.pop(app)
			except KeyError:
				pass
		_save_file_associations()
		show_alert('%s was updated.' % new_name)
	def on_cancelled(self):
		Configure(self._files).show()

class RemoveApp(QuicksearchScreen):
	def __init__(self, files):
		super().__init__()
		self._files = files
	def get_options(self):
		yield from sorted(_load_apps())
	def on_selected(self, app):
		apps = _load_apps()
		del apps[app]
		_save_apps()
		associations = _load_file_associations()
		for suffix, apps in list(associations.items()):
			apps.pop(app, None)
			if not apps:
				del associations[suffix]
		_save_file_associations()
		show_alert('%s was removed from your favorite apps.' % app)
	def on_cancelled(self):
		Configure(self._files).show()

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

class none(DirectoryPaneCommand):
	"""
	Assign key bindings to this command to effectively deactivate them.
	This is a DirectoryPaneCommand because ApplicationCommand currently does not
	support is_visible().
	"""
	def __call__(self):
		pass
	def is_visible(self):
		return False

if PLATFORM == 'Mac':
	class QuickLook(DirectoryPaneCommand):

		aliases = ('Quick Look',)

		def __call__(self):
			files = self.get_chosen_files()
			if not files:
				show_alert('No file is selected!')
				return
			if any(not is_file_url(f) for f in files):
				show_alert('Sorry, can only preview normal files.')
				return
			args = ['qlmanage', '-p']
			args.extend(map(as_human_readable, files))
			Popen(args, stdout=DEVNULL, stderr=DEVNULL)

if PLATFORM == 'Windows':
	class GoToRootOfCurrentDrive(DirectoryPaneCommand):
		def __call__(self):
			url = self.pane.get_path()
			scheme = splitscheme(url)[0]
			if scheme == 'file://':
				dest = as_url(PurePath(as_human_readable(url)).anchor)
			else:
				dest = scheme
			try:
				self.pane.set_path(dest)
			except FileNotFoundError:
				pass