from core.commands.external import OpenNativeFileManager
from core.tests.commands import FakePane
from fman import PLATFORM
from fman.url import as_human_readable
from unittest import TestCase, skipUnless
from unittest.mock import patch


class _FakePane(FakePane):
	def get_path(self):
		return self._url


class OpenNativeFileManagerTest(TestCase):
	def test_file_url_opens_native_file_manager(self):
		url = 'file://C:/Temp'
		with patch('core.commands.external.open_native_file_manager') as open_fm, \
				patch('core.commands.external.show_alert') as show_alert:
			OpenNativeFileManager(_FakePane(url=url))()
		open_fm.assert_called_once_with(as_human_readable(url))
		show_alert.assert_not_called()

	def test_non_file_url_shows_alert(self):
		with patch('core.commands.external.open_native_file_manager') as open_fm, \
				patch('core.commands.external.show_alert') as show_alert:
			OpenNativeFileManager(_FakePane(url='zip://C:/a.zip'))()
		open_fm.assert_not_called()
		show_alert.assert_called_once()

	@skipUnless(PLATFORM == 'Windows', 'network:// only exists on Windows')
	def test_network_overview_opens_explorer_network_page(self):
		with patch('core.commands.external.open_native_file_manager') as open_fm, \
				patch('core.commands.external.show_alert') as show_alert:
			OpenNativeFileManager(_FakePane(url='network://'))()
		open_fm.assert_called_once_with('shell:NetworkPlacesFolder')
		show_alert.assert_not_called()

	@skipUnless(PLATFORM == 'Windows', 'network:// only exists on Windows')
	def test_network_server_opens_unc_path(self):
		with patch('core.commands.external.open_native_file_manager') as open_fm, \
				patch('core.commands.external.show_alert') as show_alert:
			OpenNativeFileManager(_FakePane(url='network://SERVER1'))()
		open_fm.assert_called_once_with(r'\\SERVER1')
		show_alert.assert_not_called()
