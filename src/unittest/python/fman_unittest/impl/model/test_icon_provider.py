from fman import PLATFORM
from fman.impl.model.icon_provider import IconProvider
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, skipIf
from unittest.mock import patch

@skipIf(PLATFORM != 'Windows', 'Skip Windows-only test')
class NetworkIconTest(TestCase):

	"""
	Asking the Windows shell for a file's icon on a network share reads that
	file over the wire. Default to the cheap per-extension icon there; the Core
	plugin's ToggleNetworkIcons command opts back in.
	"""

	_LOCAL = 'file://C:/dir/adb.exe'
	_NETWORK = 'file:////tsclient/C/dir/adb.exe'

	def test_local_file_uses_shell_icon(self):
		self.assertEqual('C:/dir/adb.exe', self._get_icon(self._LOCAL))
	def test_network_file_uses_generic_icon(self):
		self.assertEqual(self._surrogate('.exe'), self._get_icon(self._NETWORK))
	def test_network_file_reuses_one_icon_per_suffix(self):
		self._get_icon(self._NETWORK)
		other = 'file:////tsclient/C/other/fastboot.exe'
		self.assertEqual(self._surrogate('.exe'), self._get_icon(other))
	def test_network_file_uses_shell_icon_when_enabled(self):
		icon = self._get_icon(self._NETWORK, network_file_icons=True)
		self.assertEqual('//tsclient/C/dir/adb.exe', icon)
	def _get_icon(self, url, **settings):
		with patch(
			'fman.impl.model.icon_provider.load_json', return_value=settings
		):
			return self._provider.get_icon(url)
	def _surrogate(self, suffix):
		return Path(self._cache_dir.name, 'file' + suffix).as_posix()
	def setUp(self):
		super().setUp()
		self._cache_dir = TemporaryDirectory()
		self.addCleanup(self._cache_dir.cleanup)
		self._provider = IconProvider(
			_StubQtIconProvider(), _StubFileSystem(), self._cache_dir.name
		)

class _StubQtIconProvider:
	def icon(self, file_info):
		# The path is all we assert on - the real one returns a QIcon:
		return file_info.filePath()

class _StubFileSystem:
	def is_dir(self, url):
		return False
	def resolve(self, url):
		return url
