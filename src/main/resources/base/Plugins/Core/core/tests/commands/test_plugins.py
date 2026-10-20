from core.commands import plugins as plugins_module
from core.github import GitHubRepo
from unittest import TestCase
from unittest.mock import patch


def _repo(name='Plugin'):
	return GitHubRepo({
		'name': name, 'full_name': 'someone/' + name, 'default_branch': 'main',
		'description': 'Short summary',
		'url': 'https://api.github.com/repos/someone/' + name
	})


class PickRepoTest(TestCase):
	def setUp(self):
		self.repo = _repo()
		self.command = plugins_module.InstallPlugin(None)
		self.command._plugin_repos = [self.repo]
		patchers = [
			patch.object(plugins_module, 'show_quicksearch'),
			patch.object(plugins_module, 'show_plugin_info'),
			patch.object(plugins_module, 'StatusMessage'),
		]
		self.quicksearch, self.show_info, _ = [p.start() for p in patchers]
		for patcher in patchers:
			self.addCleanup(patcher.stop)

	def test_install_on_info_screen_returns_picked_repo(self):
		self.quicksearch.return_value = ('plug', self.repo)
		self.show_info.return_value = True
		with patch.object(self.repo, 'fetch_description', return_value='# Details'):
			self.assertIs(self.repo, self.command._pick_repo())
		self.show_info.assert_called_once_with('Plugin', '# Details')
		self.quicksearch.assert_called_once_with(
			self.command._get_matching_repos, query=''
		)

	def test_back_reopens_picker_with_previous_query(self):
		self.quicksearch.side_effect = [('plug', self.repo), ('plugin', self.repo)]
		self.show_info.side_effect = [False, True]
		with patch.object(self.repo, 'fetch_description', return_value='# Details'):
			self.assertIs(self.repo, self.command._pick_repo())
		self.assertEqual(2, self.quicksearch.call_count)
		self.assertEqual('', self.quicksearch.call_args_list[0].kwargs['query'])
		self.assertEqual('plug', self.quicksearch.call_args_list[1].kwargs['query'])

	def test_picker_cancel_does_not_show_info_screen(self):
		self.quicksearch.return_value = None
		self.assertIsNone(self.command._pick_repo())
		self.show_info.assert_not_called()

	def test_missing_description_uses_fallback_markdown(self):
		self.quicksearch.return_value = ('', self.repo)
		self.show_info.return_value = True
		with patch.object(self.repo, 'fetch_description', return_value=None):
			self.command._pick_repo()
		markdown = self.show_info.call_args.args[1]
		self.assertIn('# Plugin', markdown)
		self.assertIn('Short summary', markdown)
		self.assertIn('No description available', markdown)
