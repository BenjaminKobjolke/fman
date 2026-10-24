from fman import PLATFORM
from unittest import TestCase, skipIf

if PLATFORM == 'Windows':
	from core.fs.local.windows.drives import DriveName
else:
	DriveName = None


@skipIf(PLATFORM != 'Windows', 'drives:// only exists on Windows')
class DriveNameTest(TestCase):
	def test_does_not_query_volume_label_for_a_network_drive(self):
		from unittest.mock import patch

		class Kernel32:
			volume_info_calls = 0
			def GetDriveTypeW(self, path):
				return 4
			def GetVolumeInformationW(self, *args):
				self.volume_info_calls += 1
				return 0

		class Windll:
			kernel32 = Kernel32()

		with patch('core.fs.local.windows.drives.windll', Windll()):
			self.assertEqual('Z:', DriveName().get_str('drives://Z:'))
		self.assertEqual(0, Windll.kernel32.volume_info_calls)
