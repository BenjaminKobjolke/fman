"""File operations in folders that need administrator rights (Windows UAC).

fman runs without administrator rights, so writing into a protected folder
such as C:\\Program Files fails with PermissionError. The functions here hand
such an operation to the Windows shell instead (IFileOperation, which is what
Explorer uses): the shell raises the UAC prompt and elevates that one
operation, while fman itself stays unelevated.

Whether to go this way is decided up front, by probing the folder
(#needs_elevation), not by catching PermissionError afterwards. fman's own
machinery works file by file, which would mean one UAC prompt per file - and
PermissionError is also what a file held open by another program raises, for
which rename's Retry is the right answer.

See docs/functions/elevation.md.
"""
from core.util import _iter_parents
from fman import PLATFORM
from fman.fs import notify_file_added, notify_file_removed
from fman.url import as_human_readable, basename, dirname, join, splitscheme
from os.path import isdir, lexists
from uuid import uuid4

import os

__all__ = ['copy', 'create', 'delete', 'move', 'needs_elevation', 'rename']

def needs_elevation(*dir_urls):
	"""
	True if creating a file in any of the given local directories is denied.
	"""
	if PLATFORM != 'Windows' or not _are_local(dir_urls):
		return False
	return not all(map(_is_writable, dir_urls))

def copy(urls, dest_dir, dest_name=None):
	"""
	Returns whether the copy was handled here. If not, the caller proceeds as
	usual. The same goes for #move, #delete and #rename.
	"""
	# Reading needs no rights, so the source directories are not probed:
	if not _are_local(urls) or not needs_elevation(dest_dir):
		return False
	_transfer('CopyItem', urls, dest_dir, dest_name)
	return True

def move(urls, dest_dir, dest_name=None):
	# Unlike #copy, a move also removes the sources:
	if not needs_elevation(dest_dir, *_parents(urls)):
		return False
	_transfer('MoveItem', urls, dest_dir, dest_name)
	return True

def delete(urls, to_trash):
	if not needs_elevation(*_parents(urls)):
		return False
	def queue(op, item):
		for url in urls:
			op.DeleteItem(item(_path(url)))
	# fman has already asked, so don't let the shell ask again:
	flags = _FOF_NOCONFIRMATION | (_FOF_ALLOWUNDO if to_trash else 0)
	_perform(queue, flags)
	_notify(removed=urls)
	return True

def rename(url, new_name):
	if not needs_elevation(dirname(url)):
		return False
	_perform(lambda op, item: op.RenameItem(item(_path(url)), new_name))
	_notify(added=[join(dirname(url), new_name)], removed=[url])
	return True

def create(url, is_dir):
	"""
	Creates an empty file or a directory, as administrator. Unlike the functions
	above, this is for after the normal attempt failed with PermissionError.
	Returns whether it now exists - the user may decline the UAC prompt.
	"""
	parent = dirname(url)
	# One UAC prompt per missing level, which is rare enough to live with:
	if not lexists(_path(parent)) and not create(parent, is_dir=True):
		return False
	attributes = _FILE_ATTRIBUTE_DIRECTORY if is_dir else _FILE_ATTRIBUTE_NORMAL
	created = _perform(lambda op, item: op.NewItem(
		item(_path(parent)), attributes, basename(url), None
	))
	_notify(added=[url])
	return created

def _transfer(method_name, urls, dest_dir, dest_name):
	# The shell needs an existing folder to copy or move into:
	if not lexists(_path(dest_dir)) and not create(dest_dir, is_dir=True):
		return
	def queue(op, item):
		dest = item(_path(dest_dir))
		for url in urls:
			getattr(op, method_name)(item(_path(url)), dest, dest_name)
	_perform(queue)
	_notify(
		added=[join(dest_dir, dest_name or basename(url)) for url in urls],
		removed=urls
	)

def _perform(queue, flags=0):
	"""
	Lets `queue(op, item)` add operations to an IFileOperation `op` - `item`
	turns a path into the IShellItem its methods take - and performs them with
	the UAC prompt enabled. Returns False if the user declined or canceled.
	"""
	# Imported late like send2trash in core/trash.py: Windows only.
	import pythoncom
	from win32com.shell import shell, shellcon
	# Commands run on a worker thread, where nobody has initialized COM yet.
	# ponytail: never uninitialized - the thread lives as long as fman does.
	pythoncom.CoInitialize()
	try:
		op = pythoncom.CoCreateInstance(
			shell.CLSID_FileOperation, None, pythoncom.CLSCTX_ALL,
			shell.IID_IFileOperation
		)
		op.SetOperationFlags(
			shellcon.FOFX_SHOWELEVATIONPROMPT | shellcon.FOF_NOCONFIRMMKDIR
			| flags
		)
		queue(op, lambda path: shell.SHCreateItemFromParsingName(
			path, None, shell.IID_IShellItem
		))
		op.PerformOperations()
		return not op.GetAnyOperationsAborted()
	except pythoncom.com_error as e:
		if e.hresult in _HRESULTS_CANCELED:
			return False
		raise OSError(e.hresult, e.strerror) from e

def _notify(added=(), removed=()):
	# fman does not watch directories on Windows, so the panes only learn of
	# the change from here. The checks are because the user may have declined,
	# canceled halfway, or skipped a file in the shell's own conflict dialog.
	for url in removed:
		if not lexists(_path(url)):
			notify_file_removed(url)
	for url in added:
		if lexists(_path(url)):
			notify_file_added(url)

def _is_writable(dir_url):
	for url in _iter_parents(dir_url):
		path = _path(url)
		if isdir(path):
			break
	else:
		return True
	# Not tempfile: on Windows it answers PermissionError with thousands of
	# retries under other names. Not os.access either - it only looks at the
	# read-only attribute, not at the folder's permissions.
	probe = os.path.join(path, '.fman-%s.tmp' % uuid4().hex)
	try:
		# O_TEMPORARY deletes the file again as soon as it is closed.
		os.close(os.open(probe, os.O_CREAT | os.O_EXCL | os.O_TEMPORARY))
	except PermissionError:
		return False
	except OSError as not_a_permission_problem:
		return True
	return True

def _are_local(urls):
	return all(splitscheme(url)[0] == 'file://' for url in urls)

def _parents(urls):
	return {dirname(url) for url in urls}

def _path(url):
	return as_human_readable(url)

_FILE_ATTRIBUTE_DIRECTORY = 0x10
_FILE_ATTRIBUTE_NORMAL = 0x80
_FOF_ALLOWUNDO = 0x40
_FOF_NOCONFIRMATION = 0x10
# What a declined UAC prompt and a canceled shell dialog come back as:
# HRESULT_FROM_WIN32(ERROR_CANCELLED) and COPYENGINE_E_USER_CANCELLED.
_HRESULTS_CANCELED = (0x800704C7 - 2**32, 0x80270000 - 2**32)
