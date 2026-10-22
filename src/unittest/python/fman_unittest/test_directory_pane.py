from fman import DirectoryPane, DirectoryPaneListener
from unittest import TestCase
from unittest.mock import Mock


class RewriteCommandTest(TestCase):
	def setUp(self):
		self.pane = DirectoryPane(None, None, Mock())

	def test_returns_listener_rewrite(self):
		args = {'urls': ['ftp://host/file.txt']}

		class RewriteListener(DirectoryPaneListener):
			def on_command(self, name, args):
				if name == 'move_to_trash':
					return 'delete_permanently', args

		self.pane._add_listener(RewriteListener(self.pane))

		self.assertEqual(
			('delete_permanently', args),
			self.pane._rewrite_command('move_to_trash', args)
		)

	def test_returns_original_command_when_no_listener_rewrites_it(self):
		args = {'urls': ['file:///file.txt']}
		self.pane._add_listener(DirectoryPaneListener(self.pane))

		self.assertEqual(
			('move_to_trash', args),
			self.pane._rewrite_command('move_to_trash', args)
		)
