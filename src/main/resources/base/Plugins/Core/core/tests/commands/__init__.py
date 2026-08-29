"""Fakes shared by the command tests.

Lives here for the same reason core/commands/util.py exists: the pane-window
stub is needed by tests for commands that sit in different modules
(pane_view, opening), and a test module may not import another.
"""

class FakeWindow:
	def __init__(self, panes=()):
		self._panes = list(panes)
	def get_panes(self):
		return self._panes
