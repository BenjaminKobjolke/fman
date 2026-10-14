"""Windows-only Robocopy helpers; Win32 is loaded only when a helper is used."""

import codecs
import ctypes
from ctypes import wintypes
from collections import deque
from threading import Lock, Thread
from time import monotonic, sleep
import ntpath
import subprocess
from subprocess import DEVNULL, PIPE, STDOUT, Popen
from typing import Any, Callable, Iterable


_KERNEL32: Any = None
_TAIL_LIMIT = 12000
_READ_SIZE = 4096
_POLL_INTERVAL = 0.05
_FILE_READ_ATTRIBUTES = 0x80
_FILE_SHARE_ALL = 0x7
_OPEN_EXISTING = 3
_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
_FILE_CASE_SENSITIVE_INFO = 23
_CASE_SENSITIVE_SEARCH = 1


class _CaseSensitiveInfo(ctypes.Structure):
	_fields_ = [('flags', wintypes.ULONG)]


class _FindData(ctypes.Structure):
	_fields_ = [
		('attributes', wintypes.DWORD), ('creation_time_low', wintypes.DWORD),
		('creation_time_high', wintypes.DWORD), ('access_time_low', wintypes.DWORD),
		('access_time_high', wintypes.DWORD), ('write_time_low', wintypes.DWORD),
		('write_time_high', wintypes.DWORD), ('size_high', wintypes.DWORD),
		('size_low', wintypes.DWORD), ('reserved0', wintypes.DWORD),
		('reserved1', wintypes.DWORD), ('filename', wintypes.WCHAR * 260),
		('alternate_filename', wintypes.WCHAR * 14),
	]


def api() -> Any:
	global _KERNEL32
	if _KERNEL32 is None:
		kernel = ctypes.WinDLL('kernel32', use_last_error=True)
		kernel.GetSystemDirectoryW.argtypes = (wintypes.LPWSTR, wintypes.UINT)
		kernel.GetSystemDirectoryW.restype = wintypes.UINT
		kernel.CreateFileW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
			ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE)
		kernel.CreateFileW.restype = wintypes.HANDLE
		kernel.GetFileInformationByHandleEx.argtypes = (
			wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD)
		kernel.GetFileInformationByHandleEx.restype = wintypes.BOOL
		kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
		kernel.CloseHandle.restype = wintypes.BOOL
		find_data = ctypes.POINTER(_FindData)
		kernel.FindFirstFileW.argtypes = (wintypes.LPCWSTR, find_data)
		kernel.FindFirstFileW.restype = wintypes.HANDLE
		kernel.FindNextFileW.argtypes = (wintypes.HANDLE, find_data)
		kernel.FindNextFileW.restype = wintypes.BOOL
		kernel.FindClose.argtypes = (wintypes.HANDLE,)
		kernel.FindClose.restype = wintypes.BOOL
		_KERNEL32 = kernel
	return _KERNEL32


def executable() -> str:
	"""Return the system copy so PATH cannot substitute another executable."""
	buffer = ctypes.create_unicode_buffer(32768)
	length = api().GetSystemDirectoryW(buffer, len(buffer))
	if not length or length >= len(buffer):
		raise ctypes.WinError(ctypes.get_last_error())
	return ntpath.join(buffer.value, 'robocopy.exe')


def case_sensitive(path: str) -> bool:
	"""Read the case-sensitive-directory flag without following a reparse point."""
	kernel = api()
	handle = kernel.CreateFileW(path, _FILE_READ_ATTRIBUTES, _FILE_SHARE_ALL, None,
		_OPEN_EXISTING, _FILE_FLAG_BACKUP_SEMANTICS | _FILE_FLAG_OPEN_REPARSE_POINT, None)
	if handle == wintypes.HANDLE(-1).value:
		raise ctypes.WinError(ctypes.get_last_error())
	try:
		info = _CaseSensitiveInfo()
		if not kernel.GetFileInformationByHandleEx(handle, _FILE_CASE_SENSITIVE_INFO,
				ctypes.byref(info), ctypes.sizeof(info)):
			error = ctypes.get_last_error()
			if error in (1, 50, 87):
				return False
			raise ctypes.WinError(error)
		return bool(info.flags & _CASE_SENSITIVE_SEARCH)
	finally:
		kernel.CloseHandle(handle)


def filenames(directory: str, check: Callable[[], None] = lambda: None) -> Iterable[tuple[str, str]]:
	"""Yield long and 8.3 names, closing the Win32 search handle on every exit."""
	kernel = api()
	data = _FindData()
	handle = kernel.FindFirstFileW(ntpath.join(directory, '*'), ctypes.byref(data))
	if handle == wintypes.HANDLE(-1).value:
		raise ctypes.WinError(ctypes.get_last_error())
	try:
		while True:
			check()
			name, alternate = data.filename, data.alternate_filename
			if name not in ('.', '..'):
				yield name, alternate
			if not kernel.FindNextFileW(handle, ctypes.byref(data)):
				error = ctypes.get_last_error()
				if error != 18:  # ERROR_NO_MORE_FILES
					raise ctypes.WinError(error)
				break
	finally:
		kernel.FindClose(handle)


def output_text(value: bytes | str) -> str:
	"""Decode the UTF-16 output Robocopy emits with /UNICODE."""
	if isinstance(value, bytes):
		return value.decode('utf-16-le', errors='replace').lstrip('\ufeff')
	return value.lstrip('\ufeff')


class OutputTail:
	"""Keep a bounded, thread-safe tail while the child process runs."""

	def __init__(self, limit: int = _TAIL_LIMIT) -> None:
		self._limit = limit
		self._parts: deque[str] = deque()
		self._length = 0
		self._lock = Lock()

	def append(self, text: str) -> None:
		if not text:
			return
		with self._lock:
			combined = (''.join(self._parts) + text)[-self._limit:]
			self._parts = deque((combined,))
			self._length = len(combined)

	def text(self) -> str:
		with self._lock:
			return ''.join(self._parts)


def _read_output(stream: Any, output: OutputTail) -> None:
	decoder = codecs.getincrementaldecoder('utf-16-le')('replace')
	try:
		while True:
			chunk = stream.read(_READ_SIZE)
			if not chunk:
				break
			output.append(decoder.decode(chunk))
		output.append(decoder.decode(b'', final=True))
	finally:
		stream.close()


def run(arguments: Iterable[str], check: Callable[[], None] = lambda: None,
		timeout: float | None = None) -> tuple[int, str]:
	"""Run one Robocopy process, draining output and killing it on cancel/timeout."""
	check()
	process = Popen(tuple(arguments), stdin=DEVNULL, stdout=PIPE, stderr=STDOUT,
		close_fds=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
	output = OutputTail()
	reader = Thread(target=_read_output, args=(process.stdout, output), daemon=True)
	reader.start()
	started = monotonic()
	try:
		while process.poll() is None:
			check()
			if timeout is not None and monotonic() - started >= timeout:
				raise TimeoutError('Robocopy did not finish within %s seconds.' % timeout)
			sleep(_POLL_INTERVAL)
		code = process.wait()
		reader.join(2)
		return code, output.text()
	except BaseException:
		if process.poll() is None:
			process.kill()
		process.wait()
		reader.join(2)
		raise
