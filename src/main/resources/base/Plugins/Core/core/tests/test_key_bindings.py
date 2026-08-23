from core.key_bindings import command_for_key_event, dispatch_bindable_command
from fman.impl.util.qt.key_event import QtKeyEvent
from PyQt5.QtCore import Qt
from unittest import TestCase

class CommandForKeyEventTest(TestCase):
	_BINDINGS = [
		{'keys': ['M'], 'command': 'video_mute'},
		{'keys': ['Ctrl+R'], 'command': 'video_restart'},
	]

	def test_matches_bound_command(self):
		event = QtKeyEvent(Qt.Key_M, Qt.NoModifier)
		self.assertEqual(
			'video_mute',
			command_for_key_event(event, self._BINDINGS, ('video_mute', 'video_restart')),
		)

	def test_finds_command_regardless_of_command_names_order(self):
		# video_restart's shortcut (Ctrl+R) must resolve even when it's
		# listed after video_mute in command_names.
		event = QtKeyEvent(Qt.Key_R, Qt.ControlModifier)
		self.assertEqual(
			'video_restart',
			command_for_key_event(event, self._BINDINGS, ('video_mute', 'video_restart')),
		)

	def test_no_match_returns_none(self):
		event = QtKeyEvent(Qt.Key_Z, Qt.NoModifier)
		self.assertIsNone(
			command_for_key_event(event, self._BINDINGS, ('video_mute', 'video_restart'))
		)

class DispatchBindableCommandTest(TestCase):
	def test_calls_matched_command_and_returns_true(self):
		called = []
		commands = {'video_mute': lambda: called.append('video_mute')}
		event = QtKeyEvent(Qt.Key_M, Qt.NoModifier)
		bindings = [{'keys': ['M'], 'command': 'video_mute'}]
		self.assertTrue(dispatch_bindable_command(event, bindings, commands))
		self.assertEqual(['video_mute'], called)

	def test_no_match_returns_false_without_calling_anything(self):
		called = []
		commands = {'video_mute': lambda: called.append('video_mute')}
		event = QtKeyEvent(Qt.Key_Z, Qt.NoModifier)
		bindings = [{'keys': ['M'], 'command': 'video_mute'}]
		self.assertFalse(dispatch_bindable_command(event, bindings, commands))
		self.assertEqual([], called)
