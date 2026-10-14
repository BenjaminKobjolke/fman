"""Drag selected local files to the last used app window on Windows."""
from fman import DirectoryPaneCommand, show_alert
from fbs_runtime.platform import is_windows
from fman.impl.util.qt.thread import run_in_main_thread
from fman.url import as_human_readable, splitscheme
from fman.impl.widgets import MessageBox

from collections import namedtuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox

import ctypes
import ctypes.wintypes
import os
import threading
import time

try:
	import pythoncom
except ImportError:
	pythoncom = None

__all__ = ['DragToLastUsedApp']

_Window = namedtuple(
	'_Window',
	'hwnd pid title visible minimized tool_window cloaked topmost'
)
_S_OK = 0
_DRAGDROP_S_DROP = 0x00040100
_DRAGDROP_S_CANCEL = 0x00040101
_DRAGDROP_S_USEDEFAULTCURSORS = 0x00040102
# ponytail: a fixed delay lets the target answer a few DragOver rounds; make it
# configurable only if a real app needs longer.
_DROP_DELAY = .4


class DragToLastUsedApp(DirectoryPaneCommand):
	"""Copy files to another app; elevated or non-droppable targets may fail.

	An elevated target with non-elevated fman blocks the drop (UIPI), and the
	target app must accept file drops at its window center.
	"""

	aliases = 'Drag to last used app',

	def is_visible(self):
		return is_windows()

	def __call__(self):
		cursor = self.pane.get_file_under_cursor()
		chosen = self.pane.get_selected_files() or \
		         ([cursor] if cursor else [])
		if not chosen:
			return
		if any(splitscheme(url)[0] != 'file://' for url in chosen):
			show_alert('Drag to last used app only supports local files.')
			return
		paths = [as_human_readable(url) for url in chosen]
		target = _pick_target(_enumerate_windows(), os.getpid())
		if target is None:
			show_alert('No other app window found.')
			return
		hwnd = target.hwnd
		title = target.title
		exe = _get_exe_name(target.pid)
		import win32con
		import win32gui
		win32gui.SetWindowPos(
			hwnd, win32con.HWND_TOP, 0, 0, 0, 0,
			win32con.SWP_NOMOVE | win32con.SWP_NOSIZE |
			win32con.SWP_NOACTIVATE
		)
		main_window = self.pane.window._widget
		if not _confirm_drag(main_window, len(paths), title, exe):
			return
		win32gui.SetForegroundWindow(hwnd)
		left, top, right, bottom = win32gui.GetWindowRect(hwnd)
		center = ((left + right) // 2, (top + bottom) // 2)
		if win32gui.GetAncestor(
				win32gui.WindowFromPoint(center), win32con.GA_ROOT) != hwnd:
			show_alert('The center of "%s" is covered by another window.' % title)
			return
		if _drop_files(paths, center) == 0:
			show_alert('"%s" did not accept the files.' % title)


@run_in_main_thread
def _confirm_drag(main_window, file_count, title, exe):
	file_word = 'file' if file_count == 1 else 'files'
	exe_text = ' (%s)' % exe if exe else ''
	box = MessageBox(None)
	box.setWindowFlags(box.windowFlags() | Qt.WindowStaysOnTopHint)
	box.setWindowTitle('Confirm drag')
	box.setIcon(QMessageBox.Question)
	box.setText(
		'Drag %d %s to "%s"%s?' % (file_count, file_word, title, exe_text)
	)
	box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
	box.setDefaultButton(QMessageBox.Ok)
	box.raise_()
	box.activateWindow()
	accepted = box.exec_() == QMessageBox.Ok
	if not accepted:
		main_window.raise_()
		main_window.activateWindow()
	return accepted


def _drop_decision(escape_pressed, now, drop_at):
	if escape_pressed:
		return _DRAGDROP_S_CANCEL
	if now >= drop_at:
		return _DRAGDROP_S_DROP
	return _S_OK


class _DropSource:
	_com_interfaces_ = (
		[pythoncom.IID_IDropSource] if pythoncom is not None else []
	)
	_public_methods_ = ['QueryContinueDrag', 'GiveFeedback']

	def __init__(self, drop_at):
		self._drop_at = drop_at

	def QueryContinueDrag(self, escape_pressed, key_state):
		return _drop_decision(escape_pressed, time.monotonic(), self._drop_at)

	def GiveFeedback(self, effect):
		return _DRAGDROP_S_USEDEFAULTCURSORS


@run_in_main_thread
def _drop_files(paths, point):
	import win32api
	from win32com.server.util import wrap
	from win32com.shell import shell, shellcon

	desktop = shell.SHGetDesktopFolder()
	parent = os.path.dirname(paths[0])
	parent_pidl = desktop.ParseDisplayName(0, None, parent, 0)[1]
	folder = desktop.BindToObject(parent_pidl, None, shell.IID_IShellFolder)
	children = [
		folder.ParseDisplayName(0, None, os.path.basename(path), 0)[1]
		for path in paths
	]
	data_object = folder.GetUIObjectOf(
		0, children, pythoncom.IID_IDataObject, 0
	)[1]

	original_position = win32api.GetCursorPos()
	win32api.SetCursorPos(point)
	stop_nudging = threading.Event()

	def nudge_cursor():
		started = time.monotonic()
		while (not stop_nudging.wait(.05) and
		       time.monotonic() - started < 3):
			win32api.SetCursorPos((point[0] + 1, point[1]))
			if stop_nudging.wait(.05):
				break
			win32api.SetCursorPos(point)

	nudger = threading.Thread(target=nudge_cursor, daemon=True)
	nudger.start()
	try:
		return pythoncom.DoDragDrop(
			data_object,
			wrap(_DropSource(time.monotonic() + _DROP_DELAY),
			     pythoncom.IID_IDropSource),
			shellcon.DROPEFFECT_COPY,
		)
	finally:
		stop_nudging.set()
		nudger.join(.1)
		win32api.SetCursorPos(original_position)


def _get_exe_name(pid):
	try:
		kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
		open_process = kernel32.OpenProcess
		open_process.argtypes = (ctypes.wintypes.DWORD, ctypes.wintypes.BOOL,
		                         ctypes.wintypes.DWORD)
		open_process.restype = ctypes.wintypes.HANDLE
		handle = open_process(0x1000, False, pid)
		if not handle:
			return ''
		try:
			query_image = kernel32.QueryFullProcessImageNameW
			query_image.argtypes = (
				ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD,
				ctypes.wintypes.LPWSTR, ctypes.POINTER(ctypes.wintypes.DWORD)
			)
			query_image.restype = ctypes.wintypes.BOOL
			path = ctypes.create_unicode_buffer(32768)
			length = ctypes.wintypes.DWORD(len(path))
			if not query_image(handle, 0, path, ctypes.byref(length)):
				return ''
			return os.path.basename(path.value)
		finally:
			kernel32.CloseHandle(handle)
	except Exception:
		return ''


def _get_window_pid(hwnd):
	user32 = ctypes.WinDLL('user32', use_last_error=True)
	get_window_thread_process_id = user32.GetWindowThreadProcessId
	get_window_thread_process_id.argtypes = (
		ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.DWORD)
	)
	get_window_thread_process_id.restype = ctypes.wintypes.DWORD
	pid = ctypes.wintypes.DWORD()
	get_window_thread_process_id(hwnd, ctypes.byref(pid))
	return pid.value


def _enumerate_windows():
	import win32con
	import win32gui

	windows = []

	def collect(hwnd, _):
		try:
			pid = _get_window_pid(hwnd)
			ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
			windows.append(_Window(
				hwnd,
				pid,
				win32gui.GetWindowText(hwnd),
				bool(win32gui.IsWindowVisible(hwnd)),
				bool(win32gui.IsIconic(hwnd)),
				bool(ex_style & win32con.WS_EX_TOOLWINDOW),
				_is_cloaked(hwnd),
				bool(ex_style & win32con.WS_EX_TOPMOST),
			))
		except Exception:
			# A window can disappear while EnumWindows is walking the Z-order.
			pass
		return True

	win32gui.EnumWindows(collect, None)
	return windows


def _is_cloaked(hwnd):
	try:
		cloaked = ctypes.c_int()
		result = ctypes.windll.dwmapi.DwmGetWindowAttribute(
			hwnd, 14, ctypes.byref(cloaked), ctypes.sizeof(cloaked)
		)
		return result == 0 and bool(cloaked.value)
	except (AttributeError, OSError):
		return False


def _pick_target(windows, own_pid):
	eligible = []
	for window in windows:
		# ponytail: skip minimized windows until restore-and-confirm support exists.
		if window.minimized:
			continue
		if (window.visible and not window.tool_window and not window.cloaked and
				window.title and window.pid != own_pid):
			eligible.append(window)
	return next((window for window in eligible if not window.topmost),
	            eligible[0] if eligible else None)
