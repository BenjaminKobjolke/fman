"""
"Release Notes" command: lets the user browse the bundled release notes via
the command palette's quicksearch UI, newest release first, and view the
chosen release's notes read-only in the pane's text viewer
(core.textviewer.show_text_in_viewer). Parsing/sorting/locale-fallback logic
lives in core.release_notes so it's testable without Qt; this module is the
thin fman/Qt-facing glue. See docs/CREATE_NEW_RELEASE.md for the
release_notes/ layout this reads.
"""
from core.quicksearch_matchers import contains_chars
from core.release_notes import (
	list_releases, load_release, release_notes_dir, render_notes,
)
from core.textviewer import show_text_in_viewer
from fman import DirectoryPaneCommand, QuicksearchItem, show_quicksearch

__all__ = ['ShowReleaseNotes']

class ShowReleaseNotes(DirectoryPaneCommand):

	aliases = ('Release Notes', 'Show release notes')

	def __call__(self):
		releases = self._list_releases()
		if not releases:
			return
		entries = [
			(folder, '%s_%d' % (version, build), self._release_date(folder))
			for version, build, folder in releases
		]
		result = show_quicksearch(self._get_items(entries))
		if not result:
			return
		folder = result[1]
		data = load_release(folder, self._get_locale())
		show_text_in_viewer(self.pane, render_notes(data))

	def is_visible(self):
		return bool(self._list_releases())

	def _list_releases(self):
		release_dir = release_notes_dir()
		return list_releases(release_dir) if release_dir else []

	def _release_date(self, folder):
		# en.json is always authored (docs/CREATE_NEW_RELEASE.md), so it's
		# used for the picker's date hint regardless of the viewer's own
		# locale, which is only resolved once a release is actually chosen.
		return load_release(folder, 'en').get('date', '')

	def _get_items(self, entries):
		def get_items(query):
			for folder, title, date in entries:
				match = contains_chars(title.lower(), query.lower())
				if match is not None:
					yield QuicksearchItem(folder, title, match, hint=date)
		return get_items

	def _get_locale(self):
		# Imported lazily so a missing/broken python-localization install
		# can't prevent Core's other commands from loading - this command
		# is the only thing in Core that depends on it.
		try:
			from python_localization.detection import detect_system_language
		except ImportError:
			return 'en'
		return detect_system_language(fallback='en')
