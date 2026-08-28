from core.shortcut_capture import format_key_event
from PyQt5.QtCore import Qt
from unittest import TestCase
from unittest.mock import patch

class FormatKeyEventTest(TestCase):

	"""
	What is written here is parsed back by QKeySequence and compared to the live
	key event (fman/impl/util/qt/key_event.py), so the spelling has to be the
	one that comparison expects.
	"""

	def test_a_bare_key(self):
		self.assertEqual('M', format_key_event(Qt.Key_M, Qt.NoModifier))
	def test_modifiers_come_in_one_canonical_order(self):
		# Always the same order, so two captures of the same combination
		# compare equal as strings - which is how bindings are compared.
		self.assertEqual(
			'Ctrl+Alt+Shift+P',
			format_key_event(
				Qt.Key_P,
				Qt.ShiftModifier | Qt.ControlModifier | Qt.AltModifier
			)
		)
	def test_return_is_spelled_enter(self):
		# QKeySequence would say 'Return'; QtKeyEvent.matches aliases the two,
		# and fman's own files say 'Enter'.
		self.assertEqual('Enter', format_key_event(Qt.Key_Return, Qt.NoModifier))
		self.assertEqual('Enter', format_key_event(Qt.Key_Enter, Qt.NoModifier))
	def test_page_keys_use_fmans_short_names(self):
		self.assertEqual(
			'PgDown', format_key_event(Qt.Key_PageDown, Qt.NoModifier)
		)
		self.assertEqual('PgUp', format_key_event(Qt.Key_PageUp, Qt.NoModifier))
	def test_the_numpad_is_prefixed(self):
		self.assertEqual(
			'Num+Down',
			format_key_event(Qt.Key_Down, Qt.KeypadModifier)
		)
	def test_function_keys(self):
		self.assertEqual('F5', format_key_event(Qt.Key_F5, Qt.NoModifier))

class MacTest(TestCase):

	"""
	Qt reports Cmd as ControlModifier and Ctrl as MetaModifier on Mac; the
	binding files use the physical names.
	"""

	def test_control_modifier_is_cmd(self):
		with patch('core.shortcut_capture.PLATFORM', 'Mac'):
			self.assertEqual(
				'Cmd+P', format_key_event(Qt.Key_P, Qt.ControlModifier)
			)
	def test_meta_modifier_is_ctrl(self):
		with patch('core.shortcut_capture.PLATFORM', 'Mac'):
			self.assertEqual(
				'Ctrl+P', format_key_event(Qt.Key_P, Qt.MetaModifier)
			)
