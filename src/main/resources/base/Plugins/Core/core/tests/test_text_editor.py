from core.text_editor import (
	PRESETS, build_editor_setting, format_arguments, parse_arguments,
	split_editor_setting
)
from core.util import strformat_dict_values
from fman import PLATFORM
from unittest import TestCase, skipUnless
from unittest.mock import patch


class ParseArgumentsTest(TestCase):
	def test_blank(self):
		self.assertEqual([], parse_arguments(''))
		self.assertEqual([], parse_arguments('   '))

	@skipUnless(PLATFORM == 'Windows', 'Windows command-line quoting')
	def test_parse_windows_arguments(self):
		self.assertEqual(
			['-a', 'C:\\My Files\\s.ini', '-b'],
			parse_arguments('-a "C:\\My Files\\s.ini" -b')
		)

	@skipUnless(PLATFORM == 'Windows', 'Windows command-line quoting')
	def test_format_windows_arguments_round_trip(self):
		arguments = ['-x', 'a b', '']
		self.assertEqual(arguments, parse_arguments(format_arguments(arguments)))

	def test_build_windows_setting(self):
		with patch('core.text_editor.PLATFORM', 'Windows'), \
			patch('core.os_.PLATFORM', 'Windows'):
			self.assertEqual(
				{'args': ['C:\\e.exe', '--zen-mode', '{file}']},
				build_editor_setting('C:\\e.exe', ['--zen-mode'])
			)

	def test_build_mac_setting(self):
		with patch('core.text_editor.PLATFORM', 'Mac'), \
			patch('core.os_.PLATFORM', 'Mac'):
			self.assertEqual(
				{'args': [
					'/usr/bin/open', '-a', '/A.app', '{file}', '--args',
					'--zen-mode'
				]},
				build_editor_setting('/A.app', ['--zen-mode'])
			)
			self.assertEqual(
				{'args': ['/usr/bin/open', '-a', '/A.app', '{file}']},
				build_editor_setting('/A.app', [])
			)

	def test_manual_braces_survive_file_formatting(self):
		with patch('core.text_editor.PLATFORM', 'Windows'), \
			patch('core.os_.PLATFORM', 'Windows'):
			setting = build_editor_setting('editor.exe', ['{x}'])
		self.assertEqual(
			['editor.exe', '{x}', 'f'],
			strformat_dict_values(setting, {'file': 'f'})['args']
		)

	def test_split_round_trips_windows_and_mac_settings(self):
		for platform in ('Windows', 'Mac'):
			with self.subTest(platform=platform), \
				patch('core.text_editor.PLATFORM', platform), \
				patch('core.os_.PLATFORM', platform):
				setting = build_editor_setting('/editor path', ['-x', 'a b'])
				self.assertEqual(
					('/editor path', ['-x', 'a b']),
					split_editor_setting(setting)
				)

	def test_split_existing_and_malformed_settings(self):
		with patch('core.text_editor.PLATFORM', 'Windows'):
			self.assertEqual(
				('editor.exe', []),
				split_editor_setting({'args': ['editor.exe', '{file}']})
			)
			for setting in ({}, {'args': 'x'}, None, {'args': []},
				{'args': ['editor.exe', 1]}):
				with self.subTest(setting=setting):
					self.assertEqual(('', []), split_editor_setting(setting))

	def test_presets(self):
		self.assertEqual((
			('Notepad++', ('-multiInst', '-nosession', '-notabbar')),
			('CudaText', ('-n', '-ns', '-nh')),
			('Notepad 4', ('-ns',)),
			('EmEditor', ('-nr', '-sp')),
			('Ecode', ('--zen-mode',)),
		), PRESETS)
