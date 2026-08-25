from core.fs.local.windows.network import NetworkFileSystem
from fman import PLATFORM
from unittest import TestCase, skipIf
from unittest.mock import patch

_MODULE = 'core.fs.local.windows.network'

# The shape WNetEnumResource(...) reports for RESOURCE_GLOBALNET: providers and
# domains are containers addressed by plain name, servers and shares by UNC.
_TREE = {
	None: ['Microsoft Windows Network'],
	'Microsoft Windows Network': ['WORKGROUP'],
	'WORKGROUP': [r'\\SERVER1', r'\\SERVER2'],
	r'\\SERVER1': [r'\\SERVER1\share1', r'\\SERVER1\share2'],
	r'\\SERVER2': [r'\\SERVER2\public'],
}

@skipIf(PLATFORM != 'Windows', 'network:// only exists on Windows')
class NetworkFileSystemTest(TestCase):
	def test_root_lists_servers(self):
		self.assertEqual(['SERVER1', 'SERVER2'], list(self._fs.iterdir('')))
	def test_root_does_not_open_servers(self):
		list(self._fs.iterdir(''))
		self.assertEqual(
			[None, 'Microsoft Windows Network', 'WORKGROUP'], self._opened
		)
	def test_server_lists_shares(self):
		self.assertEqual(
			['share1', 'share2'], list(self._fs.iterdir('SERVER1'))
		)
	def test_server_does_not_open_shares(self):
		list(self._fs.iterdir('SERVER1'))
		self.assertEqual([r'\\SERVER1'], self._opened)
	def setUp(self):
		self._fs = NetworkFileSystem()
		self._opened = []
		for name, replacement in (
			('WNetOpenEnum', self._open_enum),
			('WNetEnumResource', self._enum_resource),
			('WNetGetResourceInformation', lambda net_resource: None)
		):
			patcher = patch(_MODULE + '.' + name, replacement)
			patcher.start()
			self.addCleanup(patcher.stop)
	def _open_enum(self, scope, type_, usage, handle):
		name = getattr(handle, 'lpRemoteName', None)
		self._opened.append(name)
		return _FakeEnum(name)
	def _enum_resource(self, enum, count):
		return [_FakeResource(name) for name in _TREE.get(enum.name, [])]

class _FakeResource:
	def __init__(self, remote_name):
		self.lpRemoteName = remote_name

class _FakeEnum:
	def __init__(self, name):
		self.name = name
	def Close(self):
		pass
