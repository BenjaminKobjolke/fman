"""Offer the latest GitHub release through the command palette or timer."""
from core.updates import check_for_update
from fman import ApplicationCommand, NO, YES, clear_status_message, links, \
	load_json, save_json, show_alert, show_status_message
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
from urllib.error import URLError

__all__ = ['CheckForUpdates']

UPDATE_CHECK_FILE = 'Update Check.json'
CHECKING_MESSAGE = 'Checking for updates…'
UPDATE_MESSAGE = 'fman %s is available (installed: %s). Open the download page?'
CURRENT_MESSAGE = 'fman %s is up to date.'
ERROR_MESSAGE = 'Could not check for updates: %s'


class CheckForUpdates(ApplicationCommand):
	aliases = ('Check for updates',)

	def __call__(self, silent=False):
		if not silent:
			show_status_message(CHECKING_MESSAGE)
		try:
			try:
				status = check_for_update()
			except (URLError, LookupError, ValueError, KeyError) as error:
				if not silent:
					show_alert(ERROR_MESSAGE % error)
				return
			if not status.update_available:
				if not silent:
					show_alert(CURRENT_MESSAGE % status.installed)
				return
			settings = load_json(UPDATE_CHECK_FILE, default={})
			if silent and settings.get('announced') == status.latest:
				return
			settings['announced'] = status.latest
			save_json(UPDATE_CHECK_FILE)
			answer = show_alert(
				UPDATE_MESSAGE % (status.latest, status.installed),
				YES | NO, YES
			)
			if answer & YES:
				QDesktopServices.openUrl(QUrl(links.RELEASES))
		finally:
			if not silent:
				clear_status_message()
