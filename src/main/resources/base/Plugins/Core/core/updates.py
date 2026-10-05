"""Compare the installed release notes with GitHub's latest public release."""
from collections import namedtuple

from core.github import GitHubRepo
from core.release_notes import list_bundled_releases, parse_label
from fman import FMAN_VERSION, links


class UpdateStatus(namedtuple('UpdateStatus', 'installed latest')):
	@property
	def update_available(self):
		installed = parse_label(self.installed)
		latest = parse_label(self.latest)
		return installed is not None and latest is not None and latest > installed


def installed_label():
	releases = list_bundled_releases()
	if releases:
		version, build, _ = releases[0]
		return '%s_%d' % (version, build)
	return FMAN_VERSION + '_0'


def check_for_update():
	latest = GitHubRepo.fetch(links.GITHUB_REPO).get_latest_release()
	if parse_label(latest) is None:
		raise ValueError('Unexpected GitHub release tag: %r' % latest)
	return UpdateStatus(installed_label(), latest)
