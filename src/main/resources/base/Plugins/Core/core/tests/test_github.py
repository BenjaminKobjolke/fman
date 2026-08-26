from core.github import find_repos, GitHubRepo
from unittest import TestCase
from unittest.mock import patch

def _repo(name, pushed_at, num_stars=0):
	return {
		'name': name, 'full_name': 'someone/' + name, 'pushed_at': pushed_at,
		'stargazers_count': num_stars, 'description': '', 'url': ''
	}

class FindReposTest(TestCase):
	def test_orders_by_last_modified_newest_first(self):
		items = [
			_repo('Stale', '2019-01-01T00:00:00Z'),
			_repo('Fresh', '2024-06-01T12:00:00Z'),
			_repo('Middling', '2021-03-04T00:00:00Z')
		]
		self.assertEqual(
			['Fresh', 'Middling', 'Stale'],
			[repo.name for repo in self._find_repos(items)]
		)

	def test_repos_without_push_date_sort_last(self):
		items = [_repo('Empty', None), _repo('Pushed', '2019-01-01T00:00:00Z')]
		self.assertEqual(
			['Pushed', 'Empty'],
			[repo.name for repo in self._find_repos(items)]
		)

	def test_equally_recent_repos_are_ordered_by_stars(self):
		same_day = '2024-06-01T12:00:00Z'
		items = [
			_repo('Unloved', same_day, num_stars=3),
			_repo('Popular', same_day, num_stars=120),
			_repo('Liked', same_day, num_stars=17)
		]
		self.assertEqual(
			['Popular', 'Liked', 'Unloved'],
			[repo.name for repo in self._find_repos(items)]
		)

	def test_stars_never_outrank_a_more_recent_push(self):
		items = [
			_repo('PopularButStale', '2019-01-01T00:00:00Z', num_stars=900),
			_repo('FreshButUnknown', '2024-06-01T12:00:00Z', num_stars=1)
		]
		self.assertEqual(
			['FreshButUnknown', 'PopularButStale'],
			[repo.name for repo in self._find_repos(items)]
		)

	def _find_repos(self, items):
		response = {'items': items, 'total_count': len(items)}
		with patch('core.github._get_json', return_value=response):
			return find_repos(['fman', 'plugin'])

class GitHubRepoTest(TestCase):
	def test_last_modified_is_the_push_date(self):
		repo = GitHubRepo(_repo('Plugin', '2024-06-01T12:00:00Z'))
		self.assertEqual('2024-06-01T12:00:00Z', repo.last_modified)

	def test_last_modified_is_empty_when_absent(self):
		repo = GitHubRepo({'name': 'Plugin'})
		self.assertEqual('', repo.last_modified)
