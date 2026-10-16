import unittest

from robocopy_plugin.settings import Settings


class SettingsTest(unittest.TestCase):
	def test_defaults_and_switch_arguments(self):
		settings = Settings.load({})
		self.assertEqual(8, settings.threads)
		self.assertEqual(1, settings.retries)
		self.assertIn('/MT:8', settings.arguments())
		self.assertIn('/COPY:DAT', settings.arguments())
		self.assertNotIn('/Z', settings.arguments())

	def test_optional_transfer_switches(self):
		settings = Settings.load(
			{'threads': 4, 'restartable': True, 'unbuffered': True}
		)
		self.assertIn('/MT:4', settings.arguments())
		self.assertIn('/Z', settings.arguments())
		self.assertIn('/J', settings.arguments())

	def test_unsafe_or_invalid_settings_are_rejected(self):
		for value in ({'raw': '/MIR'}, {'threads': True}, {'threads': 33},
				{'retries': -1}, {'open_log_on_finish': True}, {'log_enabled': 1}):
			with self.subTest(value=value), self.assertRaises(ValueError):
				Settings.load(value)

	def test_finish_log_requires_logging(self):
		settings = Settings.load({'log_enabled': True, 'open_log_on_finish': True})
		self.assertTrue(settings.open_log_on_finish)
