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

def format_shortcut_hint(shortcuts):
	if PLATFORM == 'Mac':
		shortcuts = map(_insert_mac_key_symbols, shortcuts)
	return ', '.join(shortcuts)

def _insert_mac_key_symbols(shortcut):
	keys = shortcut.split('+')
	return ''.join(_KEY_SYMBOLS_MAC.get(key, key) for key in keys)
