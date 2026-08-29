"""Fakes shared by the command tests.

Lives here for the same reason core/commands/util.py exists: the pane and
window stubs are needed by tests for commands that sit in different modules
(pane_view, opening), and a test module may not import another.
"""

class FakeWindow:
	def __init__(self, panes=()):
		self._panes = list(panes)
	def get_panes(self):
		return self._panes

class FakePane:
	# The commands under test only ever ask a pane three things: what the
	# cursor is on, to take focus, and to run another command. Tests that
	# need more subclass this rather than starting a fourth fake.
	def __init__(self, window=None, url=None):
		self.window = window
		self.focused = False
		self.commands_run = []
		self._url = url
	def get_file_under_cursor(self):
		return self._url
	def focus(self):
		self.focused = True
	def run_command(self, name, args=None):
		self.commands_run.append(name)
