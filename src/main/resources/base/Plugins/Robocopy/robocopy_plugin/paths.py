"""Windows path validation and filesystem identity checks for transfer planning."""

import ntpath
import os
from pathlib import Path
import stat


NAME_SURROGATE = 0x20000000


def absolute_path(value: str) -> str:
	if (
		not isinstance(value, str) or not value
		or any(char in value for char in '\x00\r\n*?"')
	):
		raise ValueError('Enter an absolute Windows folder path without wildcards.')
	if value.startswith(('\\\\?\\', '\\\\.\\')):
		raise ValueError('Device and extended-namespace input paths are not supported.')
	drive, tail = ntpath.splitdrive(value)
	unc = (
		drive.startswith(('\\\\', '//'))
		and len(drive.replace('/', '\\').split('\\')) == 4
	)
	local = (
		len(drive) == 2 and drive[0].isascii()
		and drive[0].isalpha() and drive[1] == ':'
	)
	if not (unc or local) or not (tail.startswith(('\\', '/')) or unc and not tail):
		raise ValueError(
			'Use an absolute drive or UNC path, not a relative path or URL.'
		)
	if ':' in tail or unc and ':' in drive:
		raise ValueError(
			'Alternate streams and credentials in paths are not supported.'
		)
	for part in tail.replace('/', '\\').split('\\'):
		if (
			part and part not in ('.', '..')
			and (ntpath.isreserved(part) or part.endswith((' ', '.')))
		):
			raise ValueError('Unsupported Windows path component: ' + part)
	result = ntpath.normpath(value)
	if len(result.encode('utf-16-le', 'strict')) // 2 > 32760:
		raise ValueError('Path is too long.')
	return result


def from_url(value: str) -> str:
	if not isinstance(value, str) or not value.startswith('file://'):
		raise ValueError('Robocopy supports filesystem locations only.')
	path = value[7:].replace('/', '\\')
	if len(path) == 2 and path[1] == ':':
		path += '\\'
	return absolute_path(path)


def key(path: str) -> str:
	return ntpath.normcase(ntpath.normpath(path))


def contains(parent: str, child: str) -> bool:
	try:
		return ntpath.commonpath((key(parent), key(child))) == key(parent)
	except ValueError:
		return False


def related(first: str, second: str) -> bool:
	return contains(first, second) or contains(second, first)


def canonical(path: str) -> str:
	return str(Path(path).resolve(strict=False))


def identity(info: os.stat_result) -> tuple[int, int, int]:
	if not info.st_dev or not info.st_ino:
		raise ValueError('Cannot establish filesystem identity for this location.')
	return info.st_dev, info.st_ino, getattr(info, 'st_birthtime_ns', info.st_ctime_ns)


def inspect_source(path: str) -> os.stat_result:
	info = os.lstat(path)
	if (
		stat.S_ISLNK(info.st_mode)
		or getattr(info, 'st_reparse_tag', 0) & NAME_SURROGATE
	):
		raise ValueError(
			'Select actual files or folders, not symbolic links or junctions: ' + path
		)
	if not stat.S_ISREG(info.st_mode) and not stat.S_ISDIR(info.st_mode):
		raise ValueError('Unsupported source type: ' + path)
	return info
