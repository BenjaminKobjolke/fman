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
"""

from PyQt5.QtCore import QEvent, QObject, Qt, QTimer
from PyQt5.QtGui import QKeyEvent, QKeySequence
from PyQt5.QtWidgets import QApplication

from automated_screenshot_connector import (
	Command, DemoScript, Pause, PressKey, Screenshot, TypeText,
)
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

	def _send_chord(self, chord):
		seq = QKeySequence(chord)
		if seq.count() != 1:
			raise ValueError('Not a single key chord: %r' % chord)
		combo = seq[0]
		key = combo & ~_MODIFIER_MASK
		mods = Qt.KeyboardModifiers(combo & _MODIFIER_MASK)
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


# Recordable demos, keyed by the id passed as ``--automation-demo <id>``. The
# two panes are already positioned at examples/left_pane and examples/right_pane
# via the trailing command-line paths, so the script only drives the UI.
DEMOS = {
	1: DemoScript(
		id=1,
		name='overview',
		steps=(
			Pause(0.8),
			Screenshot('panes'),
			# Preview a file in the OTHER pane with fman's internal viewer,
			# while the left pane's list stays visible. Row 0 sorts to the
			# video; one Down lands on the first image.
			PressKey('Down'), Pause(0.4),
			# Open the palette, then type the command + Return to run it.
			PressKey('Ctrl+Shift+P'), Pause(0.5),
			Command('view in other'),  # palette alias 'View in other pane'
			Pause(1.0),
			Screenshot('view-image'),
			# Inline name filter: typing activates fman's FilterBar.
			TypeText('dummy_1'), Pause(0.6),
			Screenshot('filter'),
			PressKey('Escape'), Pause(0.3),
			# A real command run from the palette: select every file.
			PressKey('Ctrl+Shift+P'), Pause(0.5),
			Command('select all'),
			Pause(0.8),
			Screenshot('select-all'),
			Pause(1.0),
		),
	),
	# The longer "tour" for the README's main GIF/MP4. Its right pane is a
	# fresh empty temp dir (run_fman_demo.bat sets it up for demo id 2), so the
	# copy step is visible, repeatable, and never touches the example folders.
	2: DemoScript(
		id=2,
		name='tour',
		steps=(
			Pause(1.2),
			# Select every file with the direct shortcut (no palette).
			PressKey('Ctrl+A'), Pause(1.2),
			# Copy the selection into the empty right pane via the palette.
			# The palette is a modal dialog, so give it time to open before
			# typing, and time to close before the next beat.
			PressKey('Ctrl+Shift+P'), Pause(1.0),
			Command('copy'),         # runs Copy -> opens the destination prompt
			Pause(1.3),
			PressKey('Return'),      # confirm the destination (right pane dir)
			Pause(3.0),              # let the files copy into the right pane
			# Play the video in the right pane via the internal viewer.
			PressKey('Home'), Pause(0.7),   # cursor onto the video (row 0)
			PressKey('Ctrl+Shift+P'), Pause(1.0),
			Command('view in other'),
			Pause(4.0),              # let it play a moment
			Pause(1.0),
		),
	),
}
