import json
from pathlib import Path
import unittest

import fman


class AppNameTest(unittest.TestCase):
	def test_public_app_name_matches_build_display_name(self):
		root = Path(__file__).parents[4]
		settings = json.loads((root / 'src/build/settings/base.json').read_text())

		self.assertEqual('fman++', fman.APP_NAME)
		self.assertEqual(settings['display_name'], fman.APP_NAME)
