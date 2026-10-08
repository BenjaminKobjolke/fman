import json
from os.path import join
from tempfile import TemporaryDirectory
from unittest import TestCase

from fman.impl.util.settings import Settings


class SettingsTest(TestCase):
	def test_flush_pretty_prints_nested_json_and_round_trips(self):
		value = {'title': 'caf\u00e9', 'items': [{'enabled': True}, 1, None]}
		with TemporaryDirectory() as directory:
			path = join(directory, 'Settings.json')
			with open(path, 'w') as f:
				f.write(json.dumps(value))
			settings = Settings(path)
			settings.flush()
			with open(path, 'r') as f:
				self.assertEqual(json.dumps(value, indent=2) + '\n', f.read())
			reopened = Settings(path)
			self.assertEqual(value['title'], reopened.get('title', None))
			self.assertEqual(value['items'], reopened.get('items', None))
