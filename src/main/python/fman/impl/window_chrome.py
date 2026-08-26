"""
Whether the window shows the OS title bar, fman's own Help menu and the status
bar at the bottom, and the memory of those choices across restarts.

The menu is a Mac-only affair: ApplicationContext.help_menu_actions is empty
on every other platform, so no menu is ever built there and ToggleMenuBar is
not even registered (fman.impl.plugins.builtin). On Mac the menu bar is the
system one, at the top of the screen and never inside fman's window - which is
why MainWindow.set_menu_bar_visible hides the menu's QAction rather than the
bar.

The status bar is the plain case of the three: every platform has one, it is
an ordinary child widget (MainWindow.set_status_bar_visible just hides it), and
hiding it gives the panes its row.

The state lives here rather than in the widget because the widget cannot
answer the question early enough: ApplicationContext.main_window applies all
three *before* show(), when nothing is visible yet. Applying the title bar
after show() would also be worse than early: setWindowFlags destroys and
recreates the native window, which loses the frame position and, on Windows,
the layered-window bit setWindowOpacity rides on - see
MainWindow.set_title_bar_visible, which repairs both.
"""

# In %APPDATA%/fman/Local/Settings.json, and not Core Settings.json, because
# the flags are set before any plugin (and thus fman.load_json) exists - the
# same reason themes.THEME_SETTING gives. Absent means "visible": only the
# non-default False is ever written, so the file does not carry the default
# around.
TITLE_BAR_SETTING = 'title_bar_visible'
MENU_BAR_SETTING = 'menu_bar_visible'
STATUS_BAR_SETTING = 'status_bar_visible'

class WindowChrome:
	def __init__(self, settings):
		self._settings = settings
	def is_title_bar_visible(self):
		return self._settings.get(TITLE_BAR_SETTING, True)
	def is_menu_bar_visible(self):
		return self._settings.get(MENU_BAR_SETTING, True)
	def is_status_bar_visible(self):
		return self._settings.get(STATUS_BAR_SETTING, True)
	def toggle_title_bar(self, window):
		visible = not self.is_title_bar_visible()
		window.set_title_bar_visible(visible)
		self._save(TITLE_BAR_SETTING, visible)
	def toggle_menu_bar(self, window):
		visible = not self.is_menu_bar_visible()
		window.set_menu_bar_visible(visible)
		self._save(MENU_BAR_SETTING, visible)
	def toggle_status_bar(self, window):
		visible = not self.is_status_bar_visible()
		window.set_status_bar_visible(visible)
		self._save(STATUS_BAR_SETTING, visible)
	def apply(self, window):
		window.set_title_bar_visible(self.is_title_bar_visible())
		window.set_menu_bar_visible(self.is_menu_bar_visible())
		window.set_status_bar_visible(self.is_status_bar_visible())
	def _save(self, setting, visible):
		if visible:
			self._settings.pop(setting)
		else:
			self._settings[setting] = False
		self._settings.flush()
