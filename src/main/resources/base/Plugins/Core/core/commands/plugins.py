"""Installing, removing, listing and reloading fman plugins.

Installing unloads every plugin after the new one in the load order and loads
them again, so the new plugin lands in the right place. Pane paths are saved
across that (`PreservePanePaths`) because a filesystem that is reloaded takes
the location displaying it down with it.
"""
from core.github import find_repos, GitHubRepo
from core.quicksearch_matchers import contains_chars
from core.util import listdir_absolute
from fman import ApplicationCommand, DATA_DIRECTORY, DirectoryPaneCommand, \
	QuicksearchItem, clear_status_message, load_plugin, show_alert, \
	show_quicksearch, show_status_message, unload_plugin
from fman.fs import copy, delete, exists, iterdir
from fman.url import as_url, join
from tempfile import TemporaryDirectory
from urllib.error import URLError

import json
import os
import os.path

__all__ = [
	'InstallPlugin', 'ListPlugins', 'PreservePanePaths', 'ReloadPlugins',
	'RemovePlugin', 'StatusMessage'
]

def _matches_query(name, query):
	# The highlight for `name`, or None if it does not match. An empty query
	# matches everything - and contains_chars answers it with an empty
	# highlight, which is falsy, hence the explicit test.
	match = contains_chars(name.lower(), query.lower())
	if match or not query:
		return match
	return None

class InstallPlugin(ApplicationCommand):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._plugin_repos = None
	def __call__(self, github_repo=None):
		if github_repo:
			with StatusMessage('Fetching GitHub repo %s...' % github_repo):
				repo = GitHubRepo.fetch(github_repo)
		else:
			if self._plugin_repos is None:
				with StatusMessage('Fetching available plugins...'):
					try:
						self._plugin_repos = \
							find_repos(topics=['fman', 'plugin'])
					except URLError as e:
						show_alert(
							'Could not fetch available plugins: %s.' % e.reason
						)
						return
			result = show_quicksearch(self._get_matching_repos)
			repo = result[1] if result else None
		if repo:
			with StatusMessage('Downloading %s...' % repo.name):
				try:
					ref = repo.get_latest_release()
				except LookupError as no_release_yet:
					ref = repo.get_latest_commit()
				zipball_contents = repo.download_zipball(ref)
			plugin_dir = self._install_plugin(repo.name, zipball_contents)
			# Save some data in case we want to update the plugin later:
			self._record_plugin_installation(plugin_dir, repo.url, ref)
			success = self._load_installed_plugin(plugin_dir)
			if success:
				show_alert('Plugin %r was successfully installed.' % repo.name)
	def _get_matching_repos(self, query):
		installed_plugins = set(
			os.path.basename(plugin_dir)
			for plugin_dir in _get_thirdparty_plugins()
		)
		for repo in self._plugin_repos:
			if repo.name in installed_plugins:
				continue
			match = _matches_query(repo.name, query)
			if match is not None:
				hint = '%d ★' % repo.num_stars if repo.num_stars else ''
				yield QuicksearchItem(
					repo, repo.name, match, hint=hint,
					description=repo.description
				)
	def _install_plugin(self, name, zipball_contents):
		os.makedirs(_THIRDPARTY_PLUGINS_DIR, exist_ok=True)
		dest_dir = os.path.join(_THIRDPARTY_PLUGINS_DIR, name)
		dest_dir_url = as_url(dest_dir)
		if exists(dest_dir_url):
			raise ValueError('Plugin %s seems to already be installed.' % name)
		# We purposely don't use Python's ZipFile here because it does not
		# preserve the executable bit of extracted files. This would present a
		# problem for plugins shipping with their own binaries.
		with TemporaryDirectory() as tmp_dir:
			zip_path = os.path.join(tmp_dir, 'plugin.zip')
			with open(zip_path, 'wb') as f:
				f.write(zipball_contents)
			zip_url = as_url(zip_path, 'zip://')
			dir_in_zip, = iterdir(zip_url)
			copy(join(zip_url, dir_in_zip), dest_dir_url)
		return dest_dir
	def _load_installed_plugin(self, plugin_dir):
		# Unload plugins later than the given plugin in the load order, load
		# the plugin, then load the unloaded plugins again. This inserts the
		# given plugin in the correct place in the load order.
		plugins = _get_plugins()
		plugin_index = plugins.index(plugin_dir)
		to_unload = plugins[plugin_index + 1:]
		with PreservePanePaths(self.window):
			for plugin in reversed(to_unload):
				try:
					unload_plugin(plugin)
				except ValueError as was_not_loaded:
					pass
			result = load_plugin(plugin_dir)
			for plugin in to_unload:
				load_plugin(plugin)
		return result
	def _record_plugin_installation(self, plugin_dir, repo_url, ref):
		plugin_json = os.path.join(plugin_dir, 'Plugin.json')
		if os.path.exists(plugin_json):
			with open(plugin_json, 'r') as f:
				data = json.load(f)
		else:
			data = {}
		data['url'] = repo_url
		data['ref'] = ref
		with open(plugin_json, 'w') as f:
			json.dump(data, f)

_THIRDPARTY_PLUGINS_DIR = os.path.join(DATA_DIRECTORY, 'Plugins', 'Third-party')

def _get_thirdparty_plugins():
	return _list_plugins(_THIRDPARTY_PLUGINS_DIR)

def _list_plugins(dir_path):
	try:
		return list(filter(os.path.isdir, listdir_absolute(dir_path)))
	except FileNotFoundError:
		return []

class RemovePlugin(ApplicationCommand):

	aliases = ('Remove plugin',)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._installed_plugins = None
	def __call__(self):
		self._installed_plugins = _get_thirdparty_plugins()
		if not self._installed_plugins:
			show_alert("You don't seem to have any plugins installed.")
		else:
			result = show_quicksearch(self._get_matching_plugins)
			if result:
				plugin_dir = result[1]
				if plugin_dir:
					try:
						unload_plugin(plugin_dir)
					except ValueError as plugin_was_not_loaded:
						pass
					delete(as_url(plugin_dir))
					show_alert(
						'Plugin %r was successfully removed.'
						% os.path.basename(plugin_dir)
					)
	def _get_matching_plugins(self, query):
		for plugin_dir in self._installed_plugins:
			plugin_name = os.path.basename(plugin_dir)
			match = _matches_query(plugin_name, query)
			if match is not None:
				yield QuicksearchItem(plugin_dir, plugin_name, highlight=match)

class ReloadPlugins(ApplicationCommand):
	def __call__(self):
		plugins = _get_plugins()
		with PreservePanePaths(self.window):
			for plugin in reversed(plugins):
				try:
					unload_plugin(plugin)
				except ValueError as plugin_had_not_been_loaded:
					pass
			for plugin in plugins:
				load_plugin(plugin)
		num_plugins = len(plugins)
		plural = 's' if num_plugins > 1 else ''
		show_status_message(
			'Reloaded %d plugin%s.' % (num_plugins, plural), timeout_secs=2
		)

class PreservePanePaths:
	# When a pane is currently displaying a location with a file system that
	# is "reloaded", its location gets lost. So save the locations and
	# restore them later.
	def __init__(self, window):
		self._window = window
		self._paths_before = []
	def __enter__(self):
		self._paths_before = \
			[pane.get_path() for pane in (self._window.get_panes())]
		return self
	def __exit__(self, exc_type, exc_val, exc_tb):
		for pane, path in zip(self._window.get_panes(), self._paths_before):
			pane.set_path(path)

def _get_plugins():
	return _get_thirdparty_plugins() + _get_user_plugins()

def _get_user_plugins():
	result = []
	settings_plugin = ''
	user_plugins_dir = os.path.join(DATA_DIRECTORY, 'Plugins', 'User')
	for plugin_dir in _list_plugins(user_plugins_dir):
		if os.path.basename(plugin_dir) == 'Settings':
			settings_plugin = plugin_dir
		else:
			result.append(plugin_dir)
	# According to the fman docs, the Settings plugin is loaded last:
	if settings_plugin:
		result.append(settings_plugin)
	return result

class ListPlugins(DirectoryPaneCommand):
	def __call__(self):
		result = show_quicksearch(self._get_matching_plugins)
		if result:
			plugin_dir = result[1]
			if plugin_dir:
				self.pane.set_path(as_url(plugin_dir), onerror=None)
	def _get_matching_plugins(self, query):
		result = []
		for plugin_dir in _get_thirdparty_plugins():
			plugin_name = os.path.basename(plugin_dir)
			match = _matches_query(plugin_name, query)
			if match is not None:
				plugin_json = os.path.join(plugin_dir, 'Plugin.json')
				try:
					with open(plugin_json, 'r') as f:
						ref = json.load(f).get('ref', '')
				except OSError:
					ref = ''
				is_sha = len(ref) == 40
				if is_sha:
					ref = ref[:8]
				result.append(QuicksearchItem(
					plugin_dir, plugin_name, highlight=match, hint=ref
				))
		for plugin_dir in _get_user_plugins():
			plugin_name = os.path.basename(plugin_dir)
			match = _matches_query(plugin_name, query)
			if match is not None:
				result.append(
					QuicksearchItem(plugin_dir, plugin_name, highlight=match)
				)
		return sorted(result, key=lambda qsi: qsi.title)

class StatusMessage:
	def __init__(self, message):
		self._message = message
	def __enter__(self):
		show_status_message(self._message)
	def __exit__(self, *_):
		clear_status_message()
