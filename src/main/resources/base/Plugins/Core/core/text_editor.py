"""Settings and argument helpers for external text editors.

Ported from RoyiFileManager 0.5.1–0.16.1 for the editor role only.
"""
from core.os_ import get_popen_kwargs_for_opening
from fman import PLATFORM

import ctypes
import shlex
import subprocess
from typing import Sequence


PRESETS = (
	('Notepad++', ('-multiInst', '-nosession', '-notabbar')),
	('CudaText', ('-n', '-ns', '-nh')),
	('Notepad 4', ('-ns',)),
	('EmEditor', ('-nr', '-sp')),
	('Ecode', ('--zen-mode',)),
)
MANUAL = 'Manual configuration'


def parse_arguments(text: str) -> list[str]:
	if not text.strip():
		return []
	if PLATFORM == 'Windows':
		command_line_to_argv = ctypes.windll.shell32.CommandLineToArgvW
		command_line_to_argv.restype = ctypes.POINTER(ctypes.c_wchar_p)
		command_line_to_argv.argtypes = [
			ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int)
		]
		argument_count = ctypes.c_int()
		arguments = command_line_to_argv(
			'program.exe ' + text, ctypes.byref(argument_count)
		)
		if not arguments:
			raise ctypes.WinError()
		try:
			return [arguments[index] for index in range(1, argument_count.value)]
		finally:
			ctypes.windll.kernel32.LocalFree(arguments)
	return shlex.split(text)


def format_arguments(arguments: Sequence[str]) -> str:
	if PLATFORM == 'Windows':
		return subprocess.list2cmdline(arguments)
	return shlex.join(arguments)


def build_editor_setting(
	executable: str, arguments: Sequence[str]
) -> dict[str, list[str]]:
	arguments = [argument.replace('{', '{{').replace('}', '}}')
		for argument in arguments]
	if PLATFORM == 'Mac' and arguments:
		files = ['{file}', '--args', *arguments]
	else:
		files = [*arguments, '{file}']
	return get_popen_kwargs_for_opening(files, executable)


def split_editor_setting(
	setting: object
) -> tuple[str, list[str]]:
	if not isinstance(setting, dict):
		return '', []
	arguments = setting.get('args')
	if not isinstance(arguments, list) or not arguments or not all(
		isinstance(argument, str) for argument in arguments
	):
		return '', []
	if PLATFORM == 'Mac' and arguments[:2] == ['/usr/bin/open', '-a'] \
		and len(arguments) >= 3:
		executable = arguments[2]
		try:
			marker = arguments.index('--args', 3)
		except ValueError:
			editor_arguments = []
		else:
			editor_arguments = arguments[marker + 1:]
	else:
		executable = arguments[0]
		editor_arguments = [
			argument for argument in arguments[1:]
			if '{file}' not in argument
		]
	editor_arguments = [
		argument.replace('{{', '{').replace('}}', '}')
		for argument in editor_arguments
	]
	return executable, editor_arguments
