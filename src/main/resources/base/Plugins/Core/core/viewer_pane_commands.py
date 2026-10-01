"""Global pane commands whose classes opt into use inside a viewer.

Cursor, selection and location commands would act on the hidden file list,
so viewers only offer commands with ``usable_in_viewer``. Viewer bindings and
built-in keys are handled first; this lookup handles only their fall-through.
"""
from core.key_bindings import command_for_key_event, global_command_row, \
	KEY_BINDINGS_FILE
from core.viewer_file_ops import _in_background, after_file_gone
from fman import load_json
from fman.fs import exists


def pane_command_for(pane, key_event):
	# ponytail: binding args are not forwarded. Read the matching binding here
	# if a flagged plugin command needs them; none of the Core ones does.
	return command_for_key_event(
		key_event, load_json(KEY_BINDINGS_FILE, default=[]),
		pane.get_viewer_commands()
	)


def run_pane_command(pane, name, category, on_close):
	url = pane.get_file_under_cursor()
	def work():
		# get_chosen_files prefers hidden selections over the viewed file.
		selected = pane.get_selected_files()
		if selected:
			pane.clear_selection()
		try:
			pane.run_command(name)
		finally:
			if selected:
				pane.select(selected)
		if url and not exists(url):
			after_file_gone(pane, category, on_close)
	_in_background(work)


def pane_command_actions(pane, run):
	key_bindings = load_json(KEY_BINDINGS_FILE, default=[])
	return [
		global_command_row(
			pane.get_command_aliases(name)[0], name, key_bindings,
			lambda name=name: run(name)
		)
		for name in sorted(pane.get_viewer_commands())
		if pane.is_command_visible(name)
	]
