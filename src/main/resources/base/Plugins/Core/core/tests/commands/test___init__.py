from core.commands import History, Move, OpenOrView, ShowAllPanes, \
	ShowOnlyActivePane, ViewFile, ViewFileInOtherPane, _from_human_readable, \
	get_dest_suggestion, _find_extension_start, _get_shortcuts_for_command, \
	_clamp_font_size, _MIN_PANE_FONT_SIZE, _MAX_PANE_FONT_SIZE, \
	_format_window_title, _find_column_index
from core.tests import StubUI
from core.util import filenotfounderror
from fman import OK, YES, NO, PLATFORM
from fman.url import join, as_human_readable, as_url, dirname
from PyQt5.QtWidgets import QApplication
from tempfile import NamedTemporaryFile
from unittest import TestCase
from unittest.mock import patch

import os
import os.path

# ShowOnlyActivePane is decorated with @run_in_main_thread, which needs a
# QApplication instance to exist (even though it never enters its event
# loop here, since the test runs on the same thread it dispatches to).
# Keep a module-level reference so it isn't garbage-collected:
_APP = QApplication.instance() or QApplication([])

class FindExtensionStartTest(TestCase):
	def test_no_extension(self):
		self.assertIsNone(_find_extension_start('File'))
	def test_normal_extension(self):
		self.assertEqual(4, _find_extension_start('test.zip'))
	def test_tar_xz(self):
		self.assertEqual(7, _find_extension_start('archive.tar.xz'))
	def test_tar_gz(self):
		self.assertEqual(7, _find_extension_start('archive.tar.gz'))

class ConfirmTreeOperationTest(TestCase):

	class FileSystem:
		def __init__(self, files, case_sensitive=PLATFORM == 'Linux'):
			self._files = files
			self._case_sensitive = case_sensitive

		def exists(self, url):
			try:
				self._get(url)
			except KeyError:
				return False
			return True

		def is_dir(self, url):
			try:
				file_info = self._get(url)
			except KeyError:
				raise filenotfounderror(url) from None
			return file_info['is_dir']

		def samefile(self, url1, url2):
			if not self._case_sensitive:
				url1 = url1.lower()
				url2 = url2.lower()
			return url1 == url2

		def _get(self, url):
			dict_ = self._files
			if not self._case_sensitive:
				dict_ = {k.lower(): v for k, v in self._files.items()}
				url = url.lower()
			return dict_[url]

	def test_no_files(self):
		self._expect_alert(('No file is selected!',), answer=OK)
		self._check([], None)
	def test_one_file(self):
		dest_path = as_human_readable(join(self._dest, 'a.txt'))
		sel_start = dest_path.rindex(os.sep) + 1
		self._expect_prompt(
			('Move "a.txt" to', dest_path, sel_start, sel_start + 1),
			(dest_path, True)
		)
		self._check([self._a_txt], (self._dest, 'a.txt'))
	def test_one_dir(self):
		dest_path = as_human_readable(self._dest)
		self._expect_prompt(
			('Move "a" to', dest_path, 0, None), (dest_path, True)
		)
		self._check([self._a], (self._dest, None))
	def test_rename_dir_to_uppercase(self):
		dest_path = as_human_readable(self._src)
		self._expect_prompt(
			('Move "a" to', dest_path, 0, None), ('A', True)
		)
		self._check([self._a], (self._src, 'A'), dest_dir=self._src)
	def test_two_files(self):
		dest_path = as_human_readable(self._dest)
		self._expect_prompt(
			('Move 2 files to', dest_path, 0, None), (dest_path, True)
		)
		self._check([self._a_txt, self._b_txt], (self._dest, None))
	def test_into_subfolder(self):
		dest_path = as_human_readable(join(self._dest, 'a.txt'))
		sel_start = dest_path.rindex(os.sep) + 1
		self._expect_prompt(
			('Move "a.txt" to', dest_path, sel_start, sel_start + 1),
			('a', True)
		)
		self._check([self._a_txt], (self._a, None))
	def test_overwrite_single_file(self):
		dest_url = join(self._dest, 'a.txt')
		self._fs._files[dest_url] = {'is_dir': False}
		dest_path = as_human_readable(dest_url)
		sel_start = dest_path.rindex(os.sep) + 1
		self._expect_prompt(
			('Move "a.txt" to', dest_path, sel_start, sel_start + 1),
			(dest_path, True)
		)
		self._check([self._a_txt], (self._dest, 'a.txt'))
	def test_multiple_files_over_one(self):
		dest_url = join(self._dest, 'a.txt')
		self._fs._files[dest_url] = {'is_dir': False}
		dest_path = as_human_readable(dest_url)
		self._expect_prompt(
			('Move 2 files to', as_human_readable(self._dest), 0, None),
			(dest_path, True)
		)
		self._expect_alert(
			('You cannot move multiple files to a single file!',), answer=OK
		)
		self._check([self._a_txt, self._b_txt], None)
	def test_multiple_into_self(self):
		dest_path = as_human_readable(self._a)
		self._expect_prompt(
			('Move 2 files to', dest_path, 0, None), (dest_path, True)
		)
		self._expect_alert(('You cannot move a file to itself!',), answer=OK)
		self._check([self._a_txt, self._a], None, dest_dir=self._a)
	def test_renamed_destination(self):
		dest_path = as_human_readable(join(self._dest, 'a.txt'))
		sel_start = dest_path.rindex(os.sep) + 1
		self._expect_prompt(
			('Move "a.txt" to', dest_path, sel_start, sel_start + 1),
			(as_human_readable(join(self._dest, 'z.txt')), True)
		)
		self._check([self._a_txt], (self._dest, 'z.txt'))
	def test_multiple_files_nonexistent_dest(self):
		dest_url = join(self._dest, 'dir')
		dest_path = as_human_readable(dest_url)
		self._expect_prompt(
			('Move 2 files to', as_human_readable(self._dest), 0, None),
			(dest_path, True)
		)
		self._expect_alert(
			('%s does not exist. Do you want to create it as a directory and '
			 'move the files there?' % dest_path, YES | NO, YES),
			answer=YES
		)
		self._check([self._a_txt, self._b_txt], (dest_url, None))
	def test_file_system_root(self):
		dest_path = as_human_readable(join(self._root, 'a.txt'))
		sel_start = dest_path.rindex(os.sep) + 1
		self._expect_prompt(
			('Move "a.txt" to', dest_path, sel_start, sel_start + 1),
			(dest_path, True)
		)
		self._check([self._a_txt], (self._root, 'a.txt'), dest_dir=self._root)
	def test_different_scheme(self):
		dest_path = as_human_readable(join(self._dest, 'a.txt'))
		sel_start = dest_path.rindex(os.sep) + 1
		self._expect_prompt(
			('Move "a.txt" to', dest_path, sel_start, sel_start + 1),
			(dest_path, True)
		)
		src_url = 'zip:///dest.zip/a.txt'
		src_dir = dirname(src_url)
		self._check([src_url], (self._dest, 'a.txt'), src_dir=src_dir)
	def _expect_alert(self, args, answer):
		self._ui.expect_alert(args, answer)
	def _expect_prompt(self, args, answer):
		self._ui.expect_prompt(args, answer)
	def _check(self, files, expected_result, src_dir=None, dest_dir=None):
		if src_dir is None:
			src_dir = self._src
		if dest_dir is None:
			dest_dir = self._dest
		actual_result = Move._confirm_tree_operation(
			files, dest_dir, src_dir, self._ui, self._fs
		)
		self._ui.verify_expected_dialogs_were_shown()
		self.assertEqual(expected_result, actual_result)
	def setUp(self):
		super().setUp()
		self._ui = StubUI(self)
		self._root = as_url('C:\\' if PLATFORM == 'Windows' else '/')
		self._src = join(self._root, 'src')
		self._dest = join(self._root, 'dest')
		self._a = join(self._root, 'src/a')
		self._a_txt = join(self._root, 'src/a.txt')
		self._b_txt = join(self._root, 'src/b.txt')
		self._fs = self.FileSystem({
			self._src: {'is_dir': True},
			self._dest: {'is_dir': True},
			self._a: {'is_dir': True},
			self._a_txt: {'is_dir': False},
			self._b_txt: {'is_dir': False},
		})

class GetDestSuggestionTest(TestCase):
	def test_file(self):
		file_path = os.path.join(self._root, 'file.txt')
		selection_start = file_path.rindex(os.sep) + 1
		selection_end = selection_start + len('file')
		self.assertEqual(
			(file_path, selection_start, selection_end),
			get_dest_suggestion(as_url(file_path))
		)
	def test_dir(self):
		dir_path = os.path.join(self._root, 'dir')
		selection_start = dir_path.rindex(os.sep) + 1
		selection_end = None
		self.assertEqual(
			(dir_path, selection_start, selection_end),
			get_dest_suggestion(as_url(dir_path))
		)
	def setUp(self):
		super().setUp()
		self._root = 'C:\\' if PLATFORM == 'Windows' else '/'

class FromHumanReadableTest(TestCase):
	def test_no_src_dir(self):
		path = __file__
		dir_url = as_url(os.path.dirname(path))
		self.assertEqual(
			as_url(path),
			_from_human_readable(path, dir_url, None)
		)

class GetShortcutsForCommandTest(TestCase):
	def test_no_shortcut(self):
		self._check([{'keys': ['Enter'], 'command': 'open'}], 'copy', [])
	def test_simple(self):
		self._check([{'keys': ['Enter'], 'command': 'open'}], 'open', ['Enter'])
	def test_two_shortcuts(self):
		self._check(
			[{'keys': ['Enter'], 'command': 'open'},
			 {'keys': ['Down'], 'command': 'open'}],
			'open', ['Enter', 'Down']
		)
	def test_shortcut_only_displayed_for_one_command(self):
		bindings = [
			{'keys': ['Enter'], 'command': 'open'},
			{'keys': ['Enter'], 'command': 'alternative'}
		]
		self._check(bindings, 'open', ['Enter'])
		self._check(bindings, 'alternative', [])
	def _check(self, key_bindings, command, expected_shortcuts):
		actual = list(_get_shortcuts_for_command(key_bindings, command))
		self.assertEqual(expected_shortcuts, actual)

class _FakeWidget:
	def __init__(self, visible=True):
		self._visible = visible
	def isVisible(self):
		return self._visible
	def setVisible(self, visible):
		self._visible = visible

class _FakePane:
	def __init__(self, window):
		self.window = window
		self._widget = _FakeWidget()
		self.focused = False
	def focus(self):
		self.focused = True

class _FakeWindow:
	def __init__(self, panes=()):
		self._panes = list(panes)
	def get_panes(self):
		return self._panes

def _two_pane_window():
	window = _FakeWindow()
	active, other = _FakePane(window), _FakePane(window)
	window._panes = [active, other]
	return window, active, other

class ShowOnlyActivePaneTest(TestCase):
	def test_hides_other_panes(self):
		window, active, other = _two_pane_window()
		ShowOnlyActivePane(active)()
		self.assertTrue(active._widget.isVisible())
		self.assertFalse(other._widget.isVisible())
		self.assertTrue(active.focused)
	def test_visible_only_with_multiple_panes_all_shown(self):
		window, active, other = _two_pane_window()
		self.assertTrue(ShowOnlyActivePane(active).is_visible())
		other._widget.setVisible(False)
		self.assertFalse(ShowOnlyActivePane(active).is_visible())
		window._panes = [active]
		self.assertFalse(ShowOnlyActivePane(active).is_visible())

class ShowAllPanesTest(TestCase):
	def test_restores_all_panes(self):
		window, active, other = _two_pane_window()
		other._widget.setVisible(False)
		ShowAllPanes(active)()
		self.assertTrue(active._widget.isVisible())
		self.assertTrue(other._widget.isVisible())
		self.assertTrue(active.focused)
	def test_visible_only_when_a_pane_is_hidden(self):
		window, active, other = _two_pane_window()
		self.assertFalse(ShowAllPanes(active).is_visible())
		other._widget.setVisible(False)
		self.assertTrue(ShowAllPanes(active).is_visible())

class _FakeOpenOrViewPane:
	def __init__(self, url):
		self._url = url
		self.commands_run = []
	def get_file_under_cursor(self):
		return self._url
	def run_command(self, name):
		self.commands_run.append(name)

class OpenOrViewTest(TestCase):
	def test_dispatches_by_cursor_target(self):
		cases = (
			# label, is_dir, is_viewable, expected command
			('directory', True, True, 'open'),
			('file', False, True, 'view_file'),
			('binary', False, False, 'open'),
			(None, False, True, 'open'),
		)
		for label, cursor_is_dir, viewable, expected_command in cases:
			with self.subTest(label=label, viewable=viewable):
				url = 'file://' + label if label else None
				pane = _FakeOpenOrViewPane(url)
				with patch('core.commands.is_dir', return_value=cursor_is_dir), \
						patch('core.commands._is_viewable', return_value=viewable):
					OpenOrView(pane)()
				self.assertEqual([expected_command], pane.commands_run)

	def test_non_local_url_falls_back_to_open(self):
		# Scheme check happens before _is_viewable, so a viewable-looking
		# remote file still can't be handed to the (local-only) viewer.
		pane = _FakeOpenOrViewPane('http://example.com/file.txt')
		with patch('core.commands.is_dir', return_value=False), \
				patch('core.commands._is_viewable', return_value=True):
			OpenOrView(pane)()
		self.assertEqual(['open'], pane.commands_run)

class _FakeViewFilePane:
	def __init__(self, url):
		self._url = url
	def get_file_under_cursor(self):
		return self._url

def _write_temp_file(test_case, data):
	f = NamedTemporaryFile(delete=False)
	try:
		f.write(data)
	finally:
		f.close()
	test_case.addCleanup(os.remove, f.name)
	return f.name

class ViewFileTest(TestCase):
	def test_text_file_opens_text_viewer(self):
		path = _write_temp_file(self, b'hello world')
		pane = _FakeViewFilePane(as_url(path))
		with patch('core.commands.is_dir', return_value=False), \
				patch('core.commands.show_text_viewer') as show_text_viewer, \
				patch('core.commands.show_alert') as show_alert:
			ViewFile(pane)()
		show_text_viewer.assert_called_once()
		show_alert.assert_not_called()

	def test_binary_file_shows_alert_instead_of_text_viewer(self):
		path = _write_temp_file(self, b'MZ\x00\x00binary stuff')
		pane = _FakeViewFilePane(as_url(path))
		with patch('core.commands.is_dir', return_value=False), \
				patch('core.commands.show_text_viewer') as show_text_viewer, \
				patch('core.commands.show_alert') as show_alert:
			ViewFile(pane)()
		show_text_viewer.assert_not_called()
		show_alert.assert_called_once()

class _FakeViewInOtherPane:
	def __init__(self, url, window):
		self._url = url
		self.window = window
		self.focused = False
	def get_file_under_cursor(self):
		return self._url
	def focus(self):
		self.focused = True

class ViewFileInOtherPaneTest(TestCase):
	def test_mounts_in_other_pane_without_stealing_focus(self):
		path = _write_temp_file(self, b'hello world')
		window = _FakeWindow()
		source = _FakeViewInOtherPane(as_url(path), window)
		target = _FakeViewInOtherPane(None, window)
		window._panes = [source, target]
		with patch('core.commands.is_dir', return_value=False), \
				patch('core.commands.show_text_viewer') as show_text_viewer, \
				patch('core.commands.show_alert') as show_alert:
			ViewFileInOtherPane(source)()
		# Mounted into the OTHER pane, and told not to grab keyboard focus so
		# browsing stays in the source pane.
		self.assertIs(target, show_text_viewer.call_args[0][0])
		self.assertFalse(show_text_viewer.call_args.kwargs['focus_view'])
		show_alert.assert_not_called()

	def test_single_pane_views_in_place_and_takes_focus(self):
		path = _write_temp_file(self, b'hello world')
		window = _FakeWindow()
		only = _FakeViewInOtherPane(as_url(path), window)
		window._panes = [only]
		with patch('core.commands.is_dir', return_value=False), \
				patch('core.commands.show_text_viewer') as show_text_viewer, \
				patch('core.commands.show_alert') as show_alert:
			ViewFileInOtherPane(only)()
		self.assertIs(only, show_text_viewer.call_args[0][0])
		self.assertTrue(show_text_viewer.call_args.kwargs['focus_view'])
		show_alert.assert_not_called()

	def test_validation_failure_mounts_nothing(self):
		window = _FakeWindow()
		source = _FakeViewInOtherPane(None, window)  # no file selected
		target = _FakeViewInOtherPane(None, window)
		window._panes = [source, target]
		with patch('core.commands.show_text_viewer') as show_text_viewer, \
				patch('core.commands.show_alert') as show_alert:
			ViewFileInOtherPane(source)()
		show_alert.assert_called_once()
		show_text_viewer.assert_not_called()

class ClampFontSizeTest(TestCase):
	def test_steps_up(self):
		self.assertEqual(10, _clamp_font_size(9, +1))
	def test_steps_down(self):
		self.assertEqual(8, _clamp_font_size(9, -1))
	def test_clamps_at_minimum(self):
		self.assertEqual(
			_MIN_PANE_FONT_SIZE, _clamp_font_size(_MIN_PANE_FONT_SIZE, -1)
		)
	def test_clamps_at_maximum(self):
		self.assertEqual(
			_MAX_PANE_FONT_SIZE, _clamp_font_size(_MAX_PANE_FONT_SIZE, +1)
		)

class FindColumnIndexTest(TestCase):
	_COLUMNS = ['core.Name', 'core.Size', 'core.Modified']
	def test_present(self):
		self.assertEqual(1, _find_column_index(self._COLUMNS, 'core.Size'))
	def test_absent(self):
		# The Windows drives view only has a DriveName column - Size/Modified
		# don't exist there, so toggling must not raise.
		self.assertIsNone(
			_find_column_index(['core.DriveName'], 'core.Size')
		)

class FormatWindowTitleTest(TestCase):
	def test_no_paths(self):
		self.assertEqual('fman - file manager', _format_window_title([]))
	def test_blank_paths_skipped(self):
		self.assertEqual('fman - file manager', _format_window_title(['', '']))
	def test_one_path(self):
		self.assertEqual(
			'fman - file manager - C:\\test',
			_format_window_title(['C:\\test'])
		)
	def test_two_paths(self):
		self.assertEqual(
			'fman - file manager - C:\\test | D:\\other',
			_format_window_title(['C:\\test', 'D:\\other'])
		)

class HistoryTest(TestCase):
	def test_empty_back(self):
		with self.assertRaises(ValueError):
			self._go_back()
	def test_empty_forward(self):
		with self.assertRaises(ValueError):
			self._go_forward()
	def test_single_back(self):
		self._go_to('single item')
		with self.assertRaises(ValueError):
			self._go_back()
	def test_single_forward(self):
		self._go_to('single item')
		with self.assertRaises(ValueError):
			self._go_forward()
	def test_go_back_forward(self):
		self._go_to('a', 'b', 'c')
		self.assertEqual('b', self._go_back())
		self.assertEqual('a', self._go_back())
		self.assertEqual('b', self._go_forward())
		self.assertEqual('c', self._go_forward())
	def test_go_to_after_back(self):
		self._go_to('a', 'b')
		self.assertEqual('a', self._go_back())
		self._go_to('c')
		self.assertEqual(['a', 'c'], self._history._paths)
	def setUp(self):
		super().setUp()
		self._history = History()
	def _go_back(self):
		path = self._history.go_back()
		self._history.path_changed(path)
		return path
	def _go_forward(self):
		path = self._history.go_forward()
		self._history.path_changed(path)
		return path
	def _go_to(self, *paths):
		for path in paths:
			self._history.path_changed(path)