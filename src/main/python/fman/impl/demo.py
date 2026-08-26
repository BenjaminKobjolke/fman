"""Demo playback for the automated-application-screenshots recording tool.

fman opts into that tool's contract (see the tool repo's
docs/AUTOMATION_INTERFACE.md): in demo mode it plays a scripted sequence of UI
actions and reports demo_started/screenshot/demo_ended events over a socket so
the tool can record a GIF/MP4 plus PNG stills.

The reusable step model, socket client and CLI parser come from the stdlib-only
core of the ``automated_screenshot_connector`` library (installed via
requirements/windows-debug.txt). The library also ships a Qt player, but it
hard-imports PySide6 while fman is a PyQt5 app, so ``DemoPlayer`` below is a
PyQt5 port of the library's ``KeyEventDemoPlayer``: it posts real key events to
the focused widget, which also reaches fman's modal Quicksearch dialog (command
palette / inline filter) since QTimers keep firing inside nested modal loops.

The scripts it plays live in ``demo_scripts.py``.
"""

from PyQt5.QtCore import QEvent, QObject, Qt, QTimer
from PyQt5.QtGui import QKeyEvent, QKeySequence
from PyQt5.QtWidgets import QApplication

from automated_screenshot_connector.steps import (
	CustomStep, InsertChar, PressReturn, SendKey, SendScreenshot, flatten,
)

# Let the window finish its first paint before the demo starts typing.
START_DELAY_MS = 500
# Hold the final state briefly so the recording doesn't end abruptly.
END_HOLD_MS = 1000

# All Qt keyboard-modifier bits. In PyQt5, ``QKeySequence(chord)[0]`` returns a
# single int packing the key and its modifiers; we split it with this mask
# (PySide6 returns a QKeyCombination instead, hence the connector's own player
# can't be reused verbatim).
_MODIFIER_MASK = int(
	Qt.ShiftModifier | Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier
	| Qt.KeypadModifier | Qt.GroupSwitchModifier
)


class DemoPlayer(QObject):
	"""Plays one DemoScript by posting key events, then quits the app.

	Everything runs off single-shot QTimers so the event loop never blocks and
	the UI paints exactly as it would for human input.
	"""

	def __init__(self, window, client, script, hwnd):
		super().__init__(window)
		self._window = window
		self._client = client
		self._script = script
		self._hwnd = hwnd
		self._actions = flatten(script.steps)
		self._index = 0
		self._check_chords()

	def _check_chords(self):
		"""Reject an unparsable chord now, not minutes into a recording."""
		for _, action in self._actions:
			if isinstance(action, SendKey):
				self._parse_chord(action.chord)

	def start(self):
		QTimer.singleShot(START_DELAY_MS, self._begin)

	def _begin(self):
		self._client.send_started(self._script.id, self._hwnd)
		self._advance()

	def _advance(self):
		if self._index >= len(self._actions):
			self._finish()
			return
		delay, action = self._actions[self._index]
		self._index += 1
		QTimer.singleShot(delay, lambda: self._execute(action))

	def _execute(self, action):
		if isinstance(action, InsertChar):
			self._send_char(action.char)
		elif isinstance(action, PressReturn):
			self._send_chord('Return')
		elif isinstance(action, SendKey):
			self._send_chord(action.chord)
		elif isinstance(action, SendScreenshot):
			self._client.send_screenshot(action.name)
		elif isinstance(action, CustomStep):
			# fman defines no custom steps; a Wait's delay already elapsed.
			pass
		self._advance()

	def _target(self):
		return QApplication.focusWidget() or self._window

	def _send_char(self, ch):
		# Real press+release carrying the char as text, so the file view's
		# inline filter reacts exactly as it would to human typing.
		target = self._target()
		key = self._key_of(QKeySequence(ch.upper()))
		self._post(target, QEvent.KeyPress, key, Qt.NoModifier, ch)
		self._post(target, QEvent.KeyRelease, key, Qt.NoModifier, ch)

	def _parse_chord(self, chord):
		seq = QKeySequence(chord)
		if seq.count() != 1:
			raise ValueError('Not a single key chord: %r' % chord)
		combo = seq[0]
		return combo & ~_MODIFIER_MASK, Qt.KeyboardModifiers(combo & _MODIFIER_MASK)

	def _send_chord(self, chord):
		key, mods = self._parse_chord(chord)
		target = self._target()
		self._post(target, QEvent.KeyPress, key, mods)
		self._post(target, QEvent.KeyRelease, key, mods)

	def _key_of(self, seq):
		return (seq[0] & ~_MODIFIER_MASK) if seq.count() else Qt.Key_unknown

	def _post(self, target, event_type, key, mods, text=''):
		QApplication.postEvent(target, QKeyEvent(event_type, key, mods, text))

	def _finish(self):
		self._client.send_ended(self._script.id)
		self._client.close()
		instance = QApplication.instance()
		if instance is not None:
			QTimer.singleShot(END_HOLD_MS, instance.quit)
