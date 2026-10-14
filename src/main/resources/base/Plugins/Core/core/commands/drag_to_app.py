"""Drag selected local files to the last used app window on Windows."""
from fman import DirectoryPaneCommand, show_alert
from fbs_runtime.platform import is_windows
from fman.impl.util.qt.thread import run_in_main_thread
from fman.url import as_human_readable, splitscheme
from fman.impl.widgets import MessageBox

from PyQt5.QtCore import QMimeData, Qt, QUrl
from PyQt5.QtGui import QDrag
from PyQt5.QtWidgets import QMessageBox

import ctypes
import ctypes.wintypes
import os
import threading
import time

__all__ = ['DragToLastUsedApp']


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
		hwnd, _, title, _, _, _, _ = target
		exe = _get_exe_name(target[1])
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
		import win32api
		import win32gui

		win32gui.SetForegroundWindow(hwnd)
		left, top, right, bottom = win32gui.GetWindowRect(hwnd)
		target_point = ((left + right) // 2, (top + bottom) // 2)
		cursor_position = win32api.GetCursorPos()
		mouse_thread = threading.Thread(
			target=_drive_mouse,
			args=(cursor_position, target_point),
			daemon=True
		)
		mouse_thread.start()
		_perform_ole_drag(main_window, paths)


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


class _MouseInput(ctypes.Structure):
	_fields_ = (
		('dx', ctypes.wintypes.LONG),
		('dy', ctypes.wintypes.LONG),
		('mouseData', ctypes.wintypes.DWORD),
		('dwFlags', ctypes.wintypes.DWORD),
		('time', ctypes.wintypes.DWORD),
		('dwExtraInfo', ctypes.c_size_t),
	)


class _InputUnion(ctypes.Union):
	_fields_ = (('mi', _MouseInput),)


class _Input(ctypes.Structure):
	_fields_ = (
		('type', ctypes.wintypes.DWORD),
		('input', _InputUnion),
	)


def _absolute_coordinates(point):
	user32 = ctypes.windll.user32
	virtual_left = user32.GetSystemMetrics(76)
	virtual_top = user32.GetSystemMetrics(77)
	virtual_width = user32.GetSystemMetrics(78)
	virtual_height = user32.GetSystemMetrics(79)
	x = round((point[0] - virtual_left) * 65535 / max(virtual_width - 1, 1))
	y = round((point[1] - virtual_top) * 65535 / max(virtual_height - 1, 1))
	return x, y


def _send_mouse_input(point, flags):
	x, y = _absolute_coordinates(point)
	input_ = _Input()
	input_.type = 0  # INPUT_MOUSE
	input_.input.mi = _MouseInput(x, y, 0, flags, 0, 0)
	if ctypes.windll.user32.SendInput(
		1, ctypes.byref(input_), ctypes.sizeof(input_)
	) != 1:
		raise ctypes.WinError(ctypes.get_last_error())


def _drive_mouse(start, target):
	absolute = 0x8000 | 0x4000  # MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK
	import win32api
	button_down = False
	try:
		_send_mouse_input(start, absolute | 0x0002)  # MOUSEEVENTF_LEFTDOWN
		button_down = True
		# ponytail: timing gives OLE targets time to enter and process drag-over.
		time.sleep(.05)
		for step in range(1, 11):
			point = (
				round(start[0] + (target[0] - start[0]) * step / 10),
				round(start[1] + (target[1] - start[1]) * step / 10),
			)
			_send_mouse_input(point, absolute | 0x0001)  # MOUSEEVENTF_MOVE
			time.sleep(.015)
		time.sleep(.1)
	finally:
		try:
			if button_down:
				_send_mouse_input(target, absolute | 0x0004)  # MOUSEEVENTF_LEFTUP
		finally:
			win32api.SetCursorPos(start)


@run_in_main_thread
def _perform_ole_drag(main_window, paths):
	mime_data = QMimeData()
	mime_data.setUrls([QUrl.fromLocalFile(path) for path in paths])
	drag = QDrag(main_window)
	drag.setMimeData(mime_data)
	drag.exec_(Qt.CopyAction)


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


def _enumerate_windows():
	import win32con
	import win32gui
	import win32process

	windows = []

	def collect(hwnd, _):
		try:
			_, pid = win32process.GetWindowThreadProcessId(hwnd)
			ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
			windows.append((
				hwnd,
				pid,
				win32gui.GetWindowText(hwnd),
				bool(win32gui.IsWindowVisible(hwnd)),
				bool(win32gui.IsIconic(hwnd)),
				bool(ex_style & win32con.WS_EX_TOOLWINDOW),
				_is_cloaked(hwnd),
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
	for window in windows:
		_, pid, title, visible, minimized, tool_window, cloaked = window
		# ponytail: skip minimized windows until restore-and-confirm support exists.
		if minimized:
			continue
		if visible and not tool_window and not cloaked and title and pid != own_pid:
			return window
	return None
