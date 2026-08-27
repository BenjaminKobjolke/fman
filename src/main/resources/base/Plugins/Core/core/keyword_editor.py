"""
The Shift+Enter menus behind a command palette entry: view, add and delete the
hidden search keywords of one command (see docs/COMMAND_PALETTE_KEYWORDS.md).
Both the global palette and the viewer palettes hand a command name to
edit_command_keywords; everything below is the menu chain that follows.

Edits go through core.settings, so they land in the user's own
Command Keywords.json and take effect on the next keystroke - no restart.
"""
from core.command_keywords import COMMAND_KEYWORDS_FILE
from core.quicksearch_screen import QuicksearchScreen
from core.settings import get_setting, save_setting
from fman import show_prompt, show_status_message

def edit_command_keywords(command_name, title):
	"""
	Open the per-entry menu for `command_name`. `title` is the palette row's
	own label, used to name the command in the menus.
	"""
	if not command_name:
		# Viewer entries may ship no command name (ViewerAction's default), and
		# without one there is no key to store keywords under.
		show_status_message('This entry has no command name to add keywords to.')
		return
	EntryMenu(command_name, title).show()

def get_editable_keywords(command_name):
	"""
	The keywords of `command_name` as an editable list: the merged shipped +
	user ones, which is also what gets written back - see _save.
	"""
	keywords = get_setting(COMMAND_KEYWORDS_FILE, command_name, [])
	return [
		keyword for keyword in keywords
		if isinstance(keyword, str) and keyword.strip()
	]

def _save(command_name, keywords):
	# The whole merged list, never None: fman's user file replaces its shipped
	# list for a command, and popping a key that a lower-priority file still
	# defines makes the differential write raise ValueError.
	save_setting(COMMAND_KEYWORDS_FILE, command_name, keywords)

class EntryMenu(QuicksearchScreen):

	"""
	What Shift+Enter opens. One option for now; the screen exists so further
	per-entry actions have somewhere to go.
	"""

	def __init__(self, command_name, title):
		super().__init__()
		self._command_name = command_name
		self._title = title
		self._change_keywords = 'Change keywords for "%s"' % title
	def get_options(self):
		yield self._change_keywords
	def on_selected(self, option):
		if option == self._change_keywords:
			KeywordList(self._command_name, self._title).show()

class KeywordList(QuicksearchScreen):

	_ADD = 'Add keyword...'

	def __init__(self, command_name, title):
		super().__init__()
		self._command_name = command_name
		self._title = title
	def get_options(self):
		yield self._ADD
		yield from get_editable_keywords(self._command_name)
	def on_selected(self, option):
		if option == self._ADD:
			self._add()
		else:
			KeywordMenu(self._command_name, self._title, option).show()
	def _add(self):
		keyword, ok = show_prompt('New keyword for "%s":' % self._title)
		if not ok:
			self.show()
			return
		# Lowercase because that is how keywords are matched - and how the
		# shipped file is checked in tests/test_command_keywords.py.
		keyword = keyword.strip().lower()
		keywords = get_editable_keywords(self._command_name)
		if keyword and keyword not in keywords:
			_save(self._command_name, keywords + [keyword])
		self.show()

class KeywordMenu(QuicksearchScreen):

	_DELETE = 'Delete'
	_GO_BACK = 'Go back'

	def __init__(self, command_name, title, keyword):
		super().__init__()
		self._command_name = command_name
		self._title = title
		self._keyword = keyword
	def get_options(self):
		yield self._DELETE
		yield self._GO_BACK
	def on_selected(self, option):
		if option == self._DELETE:
			_save(self._command_name, [
				keyword for keyword in get_editable_keywords(self._command_name)
				if keyword != self._keyword
			])
		self.on_cancelled()
	def on_cancelled(self):
		KeywordList(self._command_name, self._title).show()
