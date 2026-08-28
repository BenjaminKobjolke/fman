"""
"Press the shortcut" - the modal dialog the in-palette binding editor
(core/binding_editor.py) uses to read a key combination, plus the formatter that
turns the key event into the string a Key Bindings file stores ('Ctrl+Alt+P').

The formatter is the reverse of fman's own matching: QtKeyEvent.matches parses
the stored string with QKeySequence and compares it to the live event
(fman/impl/util/qt/key_event.py), so what is written here has to spell keys the
way that comparison expects - notably 'Enter', never 'Return'. QtKeyEvent's own
__str__ is not usable for this: it renders Mac modifiers as glyphs and misses
that alias.

In its own module so core/binding_editor.py stays testable without Qt.
"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
	QApplication, QDialog, QLabel, QVBoxLayout,
)

from fman import PLATFORM
from fman.impl.util.qt.thread import run_in_main_thread

# Keys that only ever modify another one: on their own they are not a shortcut,
# so the dialog keeps waiting while they are held.
_MODIFIER_KEYS = frozenset((
	Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta, Qt.Key_AltGr,
))

# fman's spelling where it differs from QKeySequence's. Enter/Return is the
# load-bearing one - see the module docstring.
_KEY_NAMES = {
	Qt.Key_Return: 'Enter',
	Qt.Key_Enter: 'Enter',
	Qt.Key_PageDown: 'PgDown',
	Qt.Key_PageUp: 'PgUp',
	Qt.Key_Insert: 'Ins',
}

@run_in_main_thread
def capture_shortcut(prompt):
	"""
	Show `prompt` and wait for one key combination. Returns it as a shortcut
	string, or None if the user pressed Escape. Escape therefore cannot itself
	be captured - that one still needs a hand-edited file.
	"""
	# Plugin commands run off the GUI thread, and a widget may only be built
	# and parented there - without this fman prints "QObject::setParent:
	# Cannot set parent, new parent is in a different thread" and the dialog
	# never appears. fman's own show_alert/show_prompt do the same thing
	# (fman/impl/widgets.py).
	dialog = _ShortcutDialog(prompt, QApplication.activeWindow())
	dialog.exec_()
	return dialog.shortcut

def format_key_event(key, modifiers):
	"""
	The shortcut string for a key plus its modifiers, e.g. 'Ctrl+Alt+P'. Keeps
	one canonical modifier order so two captures of the same combination always
	compare equal as strings - which is how bindings are compared everywhere in
	this codebase.
	"""
	parts = []
	# Qt reports Cmd as ControlModifier and Ctrl as MetaModifier on Mac; fman's
	# files use the physical names, so swap them back.
	if modifiers & Qt.ControlModifier:
		parts.append('Cmd' if PLATFORM == 'Mac' else 'Ctrl')
	if modifiers & Qt.MetaModifier:
		parts.append('Ctrl' if PLATFORM == 'Mac' else 'Meta')
	if modifiers & Qt.AltModifier:
		parts.append('Alt')
	if modifiers & Qt.ShiftModifier:
		parts.append('Shift')
	if modifiers & Qt.KeypadModifier:
		parts.append('Num')
	parts.append(_key_name(key))
	return '+'.join(parts)

def _key_name(key):
	try:
		return _KEY_NAMES[key]
	except KeyError:
		return QKeySequence(key).toString()

class _ShortcutDialog(QDialog):

	def __init__(self, prompt, parent):
		super().__init__(parent)
		self.shortcut = None
		self.setWindowTitle(prompt)
		layout = QVBoxLayout(self)
		layout.addWidget(QLabel(
			'%s\n\nPress the keys you want, or Escape to cancel.' % prompt
		))
	def keyPressEvent(self, event):
		key = event.key()
		if key in _MODIFIER_KEYS:
			# Still waiting for the key the modifiers belong to.
			return
		if key == Qt.Key_Escape:
			self.reject()
			return
		self.shortcut = format_key_event(key, event.modifiers())
		self.accept()
