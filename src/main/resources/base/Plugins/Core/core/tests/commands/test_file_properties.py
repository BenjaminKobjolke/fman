"""Tests for the Windows file properties fallback command."""

import importlib
import sys
from unittest import TestCase, skipUnless
from unittest.mock import patch

from core.commands import file_properties
from core.tests.commands import FakePane
from fman import PLATFORM, links


@skipUnless(PLATFORM == 'Windows', 'Windows shell command')
class ShowExplorerPropertiesFallbackTest(TestCase):
	def test_import_error_alert_names_module_and_issue_link(self):
		with patch.dict(sys.modules, {'core.commands.explorer_properties': None}):
			module = importlib.reload(file_properties)
		self.addCleanup(importlib.reload, module)
		with patch('core.commands.file_properties.show_alert') as show_alert:
			module.ShowExplorerProperties(FakePane())()
		message = show_alert.call_args.args[0]
		self.assertIn('core.commands.explorer_properties', message)
		self.assertIn(links.ISSUES, message)
