"""
Looks up the shortcut(s) currently bound to a command in the merged,
effective key bindings (base + platform + user overrides, as returned by
fman.load_json('Key Bindings.json')) - i.e. whatever the user actually has
configured, not a hardcoded default. Shared by the global command palette
(hint display, core/commands/__init__.py) and the text viewer (matching
keystrokes against the user's configured zoom shortcuts, and showing hints
in its own palette, core/textviewer.py). Kept in its own module since
core/commands/__init__.py imports core/textviewer.py at module load - the
reverse import would be circular.
"""
from fman import PLATFORM

# Viewer-only pseudo-commands (viewer_close, video_mute, etc.) live in their
# own file, never 'Key Bindings.json' - that one is loaded by fman's own
# sanitizer, which flags any command it doesn't recognize as a startup-alert
# error. A dedicated file sidesteps that entirely; see docs/KEYBINDINGS.md.
VIEWER_KEY_BINDINGS_FILE = 'Viewer Key Bindings.json'

_KEY_SYMBOLS_MAC = {
	'Cmd': '⌘', 'Alt': '⌥', 'Ctrl': '⌃', 'Shift': '⇧', 'Backspace': '⌫',
	'Up': '↑', 'Down': '↓', 'Left': '←', 'Right': '→', 'Enter': '↩'
}

def get_shortcuts_for_command(key_bindings, command):
	shortcuts_occupied_by_other_commands = set()
	for binding in key_bindings:
		try:
			binding_cmd = binding['command']
		except (KeyError, TypeError):
			# Malformed Key Bindings.json
			continue
		try:
			shortcut = binding['keys'][0]
		except (KeyError, IndexError, TypeError):
			# Malformed Key Bindings.json
			continue
		if not isinstance(shortcut, str):
			# Malformed Key Bindings.json
			continue
		if binding_cmd == command:
			if shortcut not in shortcuts_occupied_by_other_commands:
				yield shortcut
		shortcuts_occupied_by_other_commands.add(shortcut)

def command_for_key_event(key_event, key_bindings, command_names):
	"""
	First command in command_names whose configured shortcut matches
	key_event, else None. Generalizes core.textviewer_zoom.zoom_delta_for
	(which hardcodes the two pane-font-size commands) to an arbitrary set of
	viewer-only commands, so a viewer can look up "did this keystroke match
	one of my bindable actions?" in one call.
	"""
	for command in command_names:
		for shortcut in get_shortcuts_for_command(key_bindings, command):
			if key_event.matches(shortcut):
				return command
	return None

def dispatch_bindable_command(key_event, key_bindings, commands):
	"""
	Looks up key_event against commands (see command_for_key_event) and, if
	one matches, calls it immediately. Returns whether a command fired, so
	callers can just `if dispatch_bindable_command(...): return` from
	keyPressEvent - shared by all three viewers' keyPressEvent to avoid
	repeating the same lookup-then-call sequence in each.
	"""
	command = command_for_key_event(key_event, key_bindings, commands)
	if command is not None:
		commands[command]()
		return True
	return False

def format_shortcut_hint(shortcuts):
	if PLATFORM == 'Mac':
		shortcuts = map(_insert_mac_key_symbols, shortcuts)
	return ', '.join(shortcuts)

def _insert_mac_key_symbols(shortcut):
	keys = shortcut.split('+')
	return ''.join(_KEY_SYMBOLS_MAC.get(key, key) for key in keys)
