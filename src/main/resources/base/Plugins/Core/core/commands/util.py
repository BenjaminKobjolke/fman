from fman import PLATFORM
from fman.url import splitscheme
from getpass import getuser
from os.path import expanduser
from PyQt5.QtCore import QFileInfo

import os

if PLATFORM == 'Windows':
	import winreg

# Where Explorer records the current location of the per-user folders. The
# sibling key 'User Shell Folders' holds the same paths unexpanded
# (%USERPROFILE% and friends); this one is already resolved, so no
# expandvars() is needed.
_SHELL_FOLDERS_KEY = \
	r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
# Downloads is the odd one out: it has no legacy name in the registry, only its
# known-folder GUID. Desktop and Documents ('Personal') predate that scheme.
_DOWNLOADS = '{374DE290-123F-4565-9164-39C4925E467B}'

def _query_shell_folder(reg_name):
	try:
		with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _SHELL_FOLDERS_KEY) as key:
			return winreg.QueryValueEx(key, reg_name)[0]
	except OSError:
		return None

def shell_folder(reg_name, fallback):
	# ~/Desktop is a guess, not a fact: OneDrive's "Back up your folders"
	# relocates Desktop, Documents and Downloads into ~/OneDrive, and only the
	# registry knows where they went. Fall back to the guess off Windows, or
	# when the value is missing.
	if PLATFORM == 'Windows':
		result = _query_shell_folder(reg_name)
		if result:
			return result
	return expanduser(fallback)

def get_home():
	return expanduser('~')

def get_desktop():
	return shell_folder('Desktop', '~/Desktop')

def get_documents():
	return shell_folder('Personal', '~/Documents')

def get_downloads():
	return shell_folder(_DOWNLOADS, '~/Downloads')

def get_well_known_dirs():
	# The everyday four, as {path: name}. Both GoTo's suggestion pool and the
	# Go to X palette commands in core/commands/places.py resolve them through
	# here, so there is one answer to "where is Desktop" per machine. The names
	# make them searchable in GoTo: the home directory shows as '~', which
	# nothing you would type to find it has a letter in common with.
	return {
		get_home(): 'Home',
		get_desktop(): 'Desktop',
		get_documents(): 'Documents',
		get_downloads(): 'Downloads'
	}

def get_program_files():
	return os.environ.get('PROGRAMW6432', r'C:\Program Files')

def get_program_files_x86():
	return os.environ.get('PROGRAMFILES', r'C:\Program Files (x86)')

def get_user():
	try:
		return getuser()
	except Exception:
		return os.path.basename(expanduser('~'))

def is_hidden(file_path):
	return QFileInfo(file_path).isHidden()

def is_file_url(url):
	# Lives here rather than next to any one caller: the commands that only
	# work on local files are spread over several modules (opening, transfer,
	# window, external), and none of them may import another without making
	# core/commands/__init__.py's star imports circular.
	return splitscheme(url)[0] == 'file://'