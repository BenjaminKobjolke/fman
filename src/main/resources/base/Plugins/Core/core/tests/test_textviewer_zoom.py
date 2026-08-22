from core.textviewer_zoom import zoom_delta_for
from fman.impl.util.qt.key_event import QtKeyEvent
from PyQt5.QtCore import Qt
from unittest import TestCase

class ZoomDeltaForTest(TestCase):
	# Fake merged Key Bindings.json content, standing in for whatever the
	# user actually has configured (defaults or a rebind) - zoom_delta_for
	# must key off this, never a hardcoded Alt+Up/Alt+Down.
	_BINDINGS = [
		{'keys': ['Alt+Up'], 'command': 'increase_pane_font_size'},
		{'keys': ['Alt+Down'], 'command': 'decrease_pane_font_size'},
	]

	def test_matches_configured_increase_shortcut(self):
		event = QtKeyEvent(Qt.Key_Up, Qt.AltModifier)
		self.assertEqual(+1, zoom_delta_for(event, self._BINDINGS))

	def test_matches_configured_decrease_shortcut(self):
		event = QtKeyEvent(Qt.Key_Down, Qt.AltModifier)
		self.assertEqual(-1, zoom_delta_for(event, self._BINDINGS))

	def test_unrelated_key_does_not_match(self):
		event = QtKeyEvent(Qt.Key_A, Qt.NoModifier)
		self.assertIsNone(zoom_delta_for(event, self._BINDINGS))

	def test_follows_a_user_rebind(self):
		# The whole point: if the user rebinds the shortcut, the OLD default
		# must stop matching and the NEW one must work instead.
		rebound = [
			{'keys': ['Ctrl+K'], 'command': 'increase_pane_font_size'},
		]
		old_default = QtKeyEvent(Qt.Key_Up, Qt.AltModifier)
		new_shortcut = QtKeyEvent(Qt.Key_K, Qt.ControlModifier)
		self.assertIsNone(zoom_delta_for(old_default, rebound))
		self.assertEqual(+1, zoom_delta_for(new_shortcut, rebound))
