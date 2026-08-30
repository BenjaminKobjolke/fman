import core.commands

from unittest import TestCase

class CompatibilitySurfaceTest(TestCase):

	"""
	Splitting core/commands.py into submodules dropped every name that is not
	a command class out of the `core.commands` namespace: `import *` skips
	underscore names, and each submodule's __all__ narrows the rest away.
	Third-party plugins written against the old flat module imported those
	names, so the package resolves them lazily from its submodules instead.
	"""

	def test_private_helper(self):
		from core.commands.opening import _open_local_files
		self.assertIs(core.commands._open_local_files, _open_local_files)
	def test_public_helper_omitted_from_all(self):
		from core.commands.util import get_opposite_pane
		self.assertIs(core.commands.get_opposite_pane, get_opposite_pane)
	def test_private_base_class(self):
		from core.commands.transfer import _TreeCommand
		self.assertIs(core.commands._TreeCommand, _TreeCommand)
	def test_unknown_name_still_raises(self):
		with self.assertRaises(AttributeError):
			core.commands.no_such_name
