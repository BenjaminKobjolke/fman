"""Commands and listeners that act on the window rather than its files.

The window title is rebuilt from both panes' paths on every navigation, so
`_format_window_title` is a pure string builder kept apart from the Qt access
around it. The two icon toggles write settings the engine owns
(`fman.impl.model.icon_provider`) and then reload the panes to redraw.
"""
from core.commands.util import is_file_url
from core.panes import reload_panes
from core.settings import get_setting, save_setting
from fman import ApplicationCommand, DirectoryPaneListener, PLATFORM, \
	show_status_message
# The engine owns these: it reads the settings the two icon toggles below
# write, and never imports this plugin - so the names live there.
from fman.impl.model.icon_provider import EXECUTABLE_ICONS_KEY, \
	NETWORK_ICONS_KEY, SETTINGS_FILE as ICON_SETTINGS_FILE
from fman.impl.util.qt.thread import run_in_main_thread
from fman.url import as_human_readable

__all__ = [
	'CenterWindow', 'LocationBarListener', 'Minimize', 'ToggleExecutableIcons',
	'ToggleNetworkIcons', 'UpdateWindowTitle'
]

_WINDOW_TITLE_PREFIX = 'fman - file manager'

def _format_window_title(paths):
	# Pure string builder, kept separate from the pane/Qt access so it's
	# unit-testable without a running application.
	paths = [path for path in paths if path]
	if not paths:
		return _WINDOW_TITLE_PREFIX
	return _WINDOW_TITLE_PREFIX + ' - ' + ' | '.join(paths)

def _path_for_title(pane):
	try:
		return as_human_readable(pane.get_path())
	except Exception:
		# Some locations (e.g. 'null://') can't be turned into a human
		# path. Skip them rather than let the title update crash.
		return ''

@run_in_main_thread
def _refresh_window_title(window):
	paths = [_path_for_title(pane) for pane in window.get_panes()]
	window._widget.setWindowTitle(_format_window_title(paths))

class UpdateWindowTitle(DirectoryPaneListener):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# Set the initial title when fman starts (mirrors InitPaneFontSize),
		# then keep it in sync as either pane navigates.
		_refresh_window_title(self.pane.window)
	def on_path_changed(self):
		_refresh_window_title(self.pane.window)

class Minimize(ApplicationCommand):
	def __call__(self):
		self.window.minimize()

class CenterWindow(ApplicationCommand):

	aliases = ('Center window',)

	def __call__(self):
		self.window.center_on_screen()

class ToggleNetworkIcons(ApplicationCommand):

	aliases = ('Toggle network drive icons',)

	def __call__(self):
		show_real_icons = not _is_showing_network_icons()
		# None clears the key so the file doesn't carry the default around:
		save_setting(
			ICON_SETTINGS_FILE, NETWORK_ICONS_KEY, show_real_icons or None
		)
		reload_panes(self.window)

def _is_showing_network_icons():
	return get_setting(ICON_SETTINGS_FILE, NETWORK_ICONS_KEY, False)

class ToggleExecutableIcons(ApplicationCommand):

	aliases = ('Toggle real icons for programs and shortcuts',)

	def __call__(self):
		# An icon set draws every .exe the same. The OS icon says *which*
		# program it is, which is worth more in a folder full of them - so
		# this opts .exe and .lnk back out of the active icon set.
		use_os_icons = not _is_showing_executable_icons()
		# None clears the key so the file doesn't carry the default around:
		save_setting(
			ICON_SETTINGS_FILE, EXECUTABLE_ICONS_KEY, use_os_icons or None
		)
		reload_panes(self.window)

def _is_showing_executable_icons():
	return get_setting(ICON_SETTINGS_FILE, EXECUTABLE_ICONS_KEY, False)

class LocationBarListener(DirectoryPaneListener):
	def on_location_bar_clicked(self):
		url = self.pane.get_path()
		if is_file_url(url):
			path = as_human_readable(url)
			self.pane.run_command('go_to', {'query': path})
			ctrl = 'Cmd' if PLATFORM == 'Mac' else 'Ctrl'
			show_status_message(
				'Hint: You can also press %s+P to open GoTo. If you merely '
				'want to copy the current path, close GoTo, then press '
				'Backspace followed by F11.' % ctrl, timeout_secs=15
			)
