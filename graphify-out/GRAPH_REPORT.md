# Graph Report - fman  (2026-08-24)

## Corpus Check
- 304 files · ~120,616 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3593 nodes · 8152 edges · 205 communities (157 shown, 48 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 1078 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d0cfdc1c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- MoveFiles
- as_human_readable
- textviewer.py
- SortedFileSystemModelAT
- TableModel
- PluginErrorHandler
- core/commands/__init__.py
- FileSystem
- Tour
- test_columns.py
- Model
- QuicksearchItem
- plugin.py
- Configure
- PaneTextView
- plugin_tests/__init__.py
- DirectoryPane
- load_for_view
- DevelopmentApplicationContext
- MotherFileSystem
- DrivesFileSystem
- LocalFileSystem
- NonexistentShortcutHandler
- ServerBackend
- ZipFileSystemTest
- Task
- Column
- PaneCommandRegistry
- run_in_main_thread
- Quicksearch
- application_context.py
- Plugin
- SortedFileSystemModel
- Common Rules (All Languages)
- normalize
- Cache
- _7ZipFileSystem
- StubFileSystem
- Path
- dirname
- fman/__init__.py
- Tutorial
- _7zip
- What You Must Do When Invoked
- CachedIterator
- FileListView
- ensure_libmpv_on_path
- User
- fman/impl/view/__init__.py
- Config
- Lvl1SortValues
- ._expect
- as_url
- splitscheme
- tests/test_release_notes.py
- MainWindow
- QuicksearchItemRenderer
- Executor
- SingleRowMode
- goto.py
- DiffEntry
- _Delete
- FileTreeOperation
- .__init__
- is_mac
- ContextMenuProvider
- ExternalPlugin
- UniformRowHeights
- change_image_scale
- ProgressDialog
- WriteDifferentialJsonTest
- QtKeyEvent
- CompositeItemDelegate
- ShowAllPanes
- zip.py
- SuggestLocationsTest
- ComputeDiffTest
- f
- 8 Essential Additional Rules (must-have)
- .expanduser
- fman_integrationtest/impl/plugins/test_plugin.py
- PluginSupport
- ApplicationCommand
- is_pardir
- ResizeColumnsToContents
- DirectoryPaneListener
- core/os_.py
- SplashScreen
- join
- SortFilterTableModel
- _TreeCommand
- History
- ShowReleaseNotes
- PaneVideoView
- MessageBox
- FileWatcher
- clipboard.py
- Controller
- Worker
- SessionManager
- CursorMovement
- LocationBar
- test_videoviewer.py
- DiffEntryExtendByTest
- MakeAbsoluteTest
- fman/impl/util/__init__.py
- DragAndDrop
- commands/test___init__.py
- LoadJsonTest
- sanitize_key_bindings
- normalize
- ViewFileInOtherPane
- GetNavigationStepsTest
- RelpathTest
- Python Rules (uv)
- KeyBindings
- FileSystemWrapperTest
- build.py
- Creating a New Release
- Text viewer
- widgets.py
- TestCase
- _find_extension_start
- is_image
- _OpenInPaneCommand
- ContainsCharsAfterSeparatorTest
- StubLocalFileSystem
- HistoryTest
- SanitizeContextMenuTest
- build_number.py
- graphify reference: extra exports and benchmark
- Localization
- graphify Knowledge Graph (Optional Addon)
- ExternalPluginTest
- RecordFiles
- SuggestLocations
- FileSystem
- StubUI
- format_time
- AsFromQurlTest
- AI Workflow Rules (All Languages)
- Key bindings
- Image viewer
- Video viewer
- Prompt
- LoadSaveJsonTest
- OpenOrView
- CommandCallback
- UsageHelper
- basename
- CommandPalette
- command_for_key_event
- release_notes_dir
- graphify reference: query, path, explain
- Project Setup Scripts
- Show only active pane
- Toggle columns
- Themes
- GetMovesForTransforming
- _format_window_title
- test_local.py
- is_video
- Coding Rules (Pointer)
- CODING_RULES.md
- Open or view
- Pane font size
- View file
- Release notes
- Window title
- Splitter
- DirectoryPaneListenerTest
- fman_/__init__.py
- explorer_properties.py
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- Core
- desk.sh
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- Inject Collaborators, Don't Fold Dependencies In
- fman
- AGENTS.md
- post-commit
- extraction-spec.md
- SharedSupport/bin/fman
- usr/bin/fman
- update-fman

## God Nodes (most connected - your core abstractions)
1. `FileSystem` - 182 edges
2. `MoveFiles` - 111 edges
3. `CopyFiles` - 107 edges
4. `GitHubRepo` - 107 edges
5. `ShowExplorerProperties` - 101 edges
6. `DevelopmentApplicationContext` - 84 edges
7. `splitscheme()` - 77 edges
8. `as_url()` - 76 edges
9. `DirectoryPaneCommand` - 71 edges
10. `as_human_readable()` - 71 edges

## Surprising Connections (you probably didn't know these)
- `publish()` --calls--> `is_mac()`  [INFERRED]
  build.py → src/main/resources/base/Plugins/Core/core/os_.py
- `get_resource()` --calls--> `dirname()`  [INFERRED]
  src/integrationtest/python/fman_integrationtest/__init__.py → src/main/python/fman/url.py
- `SortedFileSystemModelAT` --uses--> `NullColumn`  [INFERRED]
  src/integrationtest/python/fman_integrationtest/impl/model/test___init__.py → src/main/python/fman/impl/plugins/builtin.py
- `SortedFileSystemModelAT` --uses--> `MotherFileSystem`  [INFERRED]
  src/integrationtest/python/fman_integrationtest/impl/model/test___init__.py → src/main/python/fman/impl/plugins/mother_fs.py
- `StubIconProvider` --uses--> `NullColumn`  [INFERRED]
  src/integrationtest/python/fman_integrationtest/impl/model/test___init__.py → src/main/python/fman/impl/plugins/builtin.py

## Import Cycles
- None detected.

## Communities (205 total, 48 thin omitted)

### Community 0 - "MoveFiles"
Cohesion: 0.04
Nodes (51): DirectoryPaneCommand, ShowExplorerProperties, About, CompareDirectories, Copy, CopyPathsToClipboard, CopyToClipboard, CreateAndEditFile (+43 more)

### Community 1 - "as_human_readable"
Cohesion: 0.06
Nodes (10): as_human_readable(), join(), ConfirmTreeOperationTest, GetShortcutsForCommandTest, CopyFilesTest, FileTreeOperationAT, MockProgressDialog, MoveFilesTest (+2 more)

### Community 2 - "textviewer.py"
Cohesion: 0.05
Nodes (52): QScrollArea, _view_file_in(), "Release Notes" command: lets the user browse the bundled release notes via the…, clamp_font_size(), Shared font-size clamp for widget zoom features: pane font size…, PaneImageView, run_in_main_thread, A minimal read-only image viewer shown inside a directory pane, in place of the… (+44 more)

### Community 3 - "SortedFileSystemModelAT"
Cohesion: 0.05
Nodes (20): CaseInsensitiveDict, _is_debugger_attached(), SortedFileSystemModelAT, StubIconProvider, RunInThreadAT, _Application, QApplication, skipIf (+12 more)

### Community 4 - "TableModel"
Cohesion: 0.05
Nodes (10): _get_move_destination(), Mixin for QAbstractTableModel. Encapsulates the logic for a table where each…, Rows, TableModel, GetMoveDestinationTest, TestCase, Row, StubSignal (+2 more)

### Community 5 - "PluginErrorHandler"
Cohesion: 0.05
Nodes (19): ExceptionHandler, ParseCSSTest, TestCase, format_traceback(), PluginErrorHandler, Copied and adapted from Python's `TracebackException`. Adds one additional…, TracebackExceptionWithTbFilter, walk_tb_with_filtering() (+11 more)

### Community 6 - "core/commands/__init__.py"
Cohesion: 0.07
Nodes (39): _apply_column_visibility(), _apply_pane_font_size(), _change_pane_font_size(), _effective_font_size(), _get_applications_directory(), _get_local_filepaths(), _get_pane_info(), _get_saved_pane_font_size() (+31 more)

### Community 7 - "FileSystem"
Cohesion: 0.08
Nodes (25): copy(), delete(), exists(), FileSystem, _get_mother_fs(), is_dir(), iterdir(), makedirs() (+17 more)

### Community 8 - "Tour"
Cohesion: 0.07
Nodes (9): underline(), CleanupGuide, AfterDialogShown, run_in_main_thread, Tour, TourController, TourStep, connect_once() (+1 more)

### Community 9 - "test_columns.py"
Cohesion: 0.08
Nodes (8): Modified, Name, Size, ColumnTest, ModifiedTest, NameTest, TestCase, SizeTest

### Community 10 - "Model"
Cohesion: 0.10
Nodes (8): _get_empty_icon(), Model, DragAndDrop, run_in_main_thread, Tells the model that the given `files` exist and the URLs given in…, The thread safety of this class works as follows: There is one (and only one)…, It would be tempting to simply use `None` as an "empty" icon. But when we do…, transaction()

### Community 11 - "QuicksearchItem"
Cohesion: 0.06
Nodes (16): QuicksearchItem, _get_plugins(), _get_thirdparty_plugins(), _get_user_plugins(), InstallPlugin, _list_plugins(), PreservePanePaths, RemovePlugin (+8 more)

### Community 12 - "plugin.py"
Cohesion: 0.08
Nodes (9): FontDatabase, FontError, run_in_main_thread, RuntimeError, ColumnWrapper, FileSystemWrapper, ListenerWrapper, Wrapper (+1 more)

### Community 13 - "Configure"
Cohesion: 0.11
Nodes (14): _add_app(), Configure, EditApp, _load_apps(), _load_file_associations(), _open_files_with_app(), OpenWith, QuicksearchScreen (+6 more)

### Community 14 - "PaneTextView"
Cohesion: 0.09
Nodes (18): QPlainTextEdit, CaretFixCssTest, TestCase, caret_fix_css(), PaneTextView, Reload-from-disk for the text viewer (core/textviewer.py): the scroll/cursor-…, Shared by manual reload (PaneTextView._revert) and auto-reload…, reload_from_disk() (+10 more)

### Community 15 - "plugin_tests/__init__.py"
Cohesion: 0.08
Nodes (9): StubCommandCallback, StubDirectoryPaneWidget, StubFontDatabase, StubTheme, PluginTest, TestCase, KeyBindingsTest, PluginTest (+1 more)

### Community 17 - "load_for_view"
Cohesion: 0.11
Nodes (19): IsEditableTest, IsTextFileTest, LoadForViewTest, TestCase, ReadTextForViewTest, _write_temp_file(), decode_for_display(), is_editable() (+11 more)

### Community 18 - "DevelopmentApplicationContext"
Cohesion: 0.07
Nodes (4): ApplicationContext, DevelopmentApplicationContext, Application, QApplication

### Community 20 - "DrivesFileSystem"
Cohesion: 0.11
Nodes (12): CopyFile, DeleteIfEmpty, StubFileSystemWatcher, DriveName, DrivesFileSystem, FileSystem, NetworkFileSystem, FileSystem (+4 more)

### Community 21 - "LocalFileSystem"
Cohesion: 0.15
Nodes (6): LocalFileSystem, MoveByCopying, FileSystem, run_in_main_thread, Task, filenotfounderror()

### Community 22 - "NonexistentShortcutHandler"
Cohesion: 0.15
Nodes (11): highlight(), NonexistentShortcutDialog, NonexistentShortcutHandler, QDialog, _get_plugin_support(), load_json(), load_plugin(), Raises ValueError if the plugin was not loaded. (+3 more)

### Community 23 - "ServerBackend"
Cohesion: 0.09
Nodes (6): AsynchronousMetrics, LoggingBackend, Metrics, MetricsError, Exception, ServerBackend

### Community 25 - "Task"
Cohesion: 0.08
Nodes (6): KeyboardInterrupt, ChildProgressDialog, StubProgressDialog, Canceled, submit_task(), Task

### Community 26 - "Column"
Cohesion: 0.09
Nodes (13): CommandRaisingError, ListenerRaisingError, NoIterdirFileSystem, NonexistentColumnFileSystem, FileSystem, TestColumn, TestCommand, TestFileSystem (+5 more)

### Community 27 - "PaneCommandRegistry"
Cohesion: 0.10
Nodes (7): ApplicationCommandRegistry, CommandRegistry, _get_default_aliases(), PaneCommandRegistry, Assumed to be instantiated in main thread - see CommandRegistry#__init__()., Assumed to be instantiated in main thread - see CommandRegistry#__init__()., ReportExceptions

### Community 29 - "Quicksearch"
Cohesion: 0.10
Nodes (8): QAbstractListModel, Div, LineEdit, QDialog, QFrame, QLineEdit, Quicksearch, QuicksearchListModel

### Community 30 - "application_context.py"
Cohesion: 0.11
Nodes (7): QFileIconProvider, FrozenApplicationContext, GnomeFileIconProvider, GnomeNotAvailable, IconProvider, RuntimeError, Settings

### Community 31 - "Plugin"
Cohesion: 0.10
Nodes (6): get_command_class_name(), _get_command_name(), Plugin, GetCommandClassNameTest, GetCommandNameTest, TestCase

### Community 32 - "SortedFileSystemModel"
Cohesion: 0.10
Nodes (3): QSortFilterProxyModel, run_in_main_thread, SortedFileSystemModel

### Community 33 - "Common Rules (All Languages)"
Cohesion: 0.07
Nodes (27): Centralized Logger — Single Off Switch, Comments Explain Why, Not What, Common Rules (All Languages), Confirm Dependency Versions, Derive, Don't Duplicate — One Value Owns the Derivation, Don't Repeat Yourself (DRY), Error Handling & Logging Strategy, Input Validation at Boundaries (+19 more)

### Community 34 - "normalize"
Cohesion: 0.11
Nodes (8): cached(), filenotfounderror(), normalize(), FileSystem, StubFileSystem, FileSystemCountingIsdirCalls, FileSystem, NormalizeTest

### Community 35 - "Cache"
Cohesion: 0.11
Nodes (4): Cache, CacheItem, CacheTest, TestCase

### Community 36 - "_7ZipFileSystem"
Cohesion: 0.15
Nodes (4): _7ZipFileSystem, _create_temp_dir_next_to(), FileSystem, _run_7zip()

### Community 37 - "StubFileSystem"
Cohesion: 0.19
Nodes (4): FileSystem, StubFileSystem, FileSystemRaisingError, MotherFileSystemTest

### Community 38 - "Path"
Cohesion: 0.14
Nodes (6): Path, LocalFileSystemTest, skipIf, TestCase, Consider moving a file from src to dst. When src and dst are on the same drive…, _urlpath()

### Community 39 - "dirname"
Cohesion: 0.18
Nodes (9): Exclude .icon from == comparisons. The reason for this is that…, Row, _add_backslash_to_drive_if_missing(), make_absolute(), parent(), Normalize "C:" -> "C:\". Required for some path functions on Windows., get_existing_pardir(), _iter_parents() (+1 more)

### Community 40 - "fman/__init__.py"
Cohesion: 0.11
Nodes (16): get_application_context(), clear_status_message(), _get_app_ctxt(), get_application_command_aliases(), get_application_commands(), _get_controller(), _get_ui(), # TODO: Rename to set_location(...) (+8 more)

### Community 41 - "Tutorial"
Cohesion: 0.14
Nodes (10): _get_navigation_steps(), _is_hidden(), _is_macos_catalina_or_later(), run_in_main_thread, Opens `self._src_url` and calls `self._navigate()` once it's loaded. The…, r""" \\server\Folder -> \\SERVER\Folder, Tutorial, _upper_server() (+2 more)

### Community 42 - "_7zip"
Cohesion: 0.10
Nodes (7): CalledProcessError, _7zip, _7zipError, When run from a terminal, 7-Zip displays progress information for some…, Run7ZipViaPty, Run7ZipViaWinpty, Stdout

### Community 43 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 44 - "CachedIterator"
Cohesion: 0.16
Nodes (4): CachedIterator, CachedIteratorTest, TestCase, Suppose each next(...) call below is in one thread and .remove(...) and…

### Community 46 - "ensure_libmpv_on_path"
Cohesion: 0.14
Nodes (13): cache_dir(), _DownloadLibmpv, ensure_libmpv_on_path(), _extract(), _prepend_to_path(), Task, Ensures the native libmpv-2.dll (required by python-mpv, see…, Blocks (on the calling background thread - see module docstring) until… (+5 more)

### Community 47 - "User"
Cohesion: 0.16
Nodes (11): decrypt(), _negate(), unpack_key(), User, parse_version(), encrypt(), EncryptionTest, generate_key() (+3 more)

### Community 48 - "fman/impl/view/__init__.py"
Cohesion: 0.11
Nodes (11): QMenu, QProxyStyle, DragAndDrop, QTableView, Layout, Menu, ProxyStyle, Set the selection and/or cursor on the given QLineEdit. The indices… (+3 more)

### Community 49 - "Config"
Cohesion: 0.13
Nodes (5): ConfigTest, TestCase, Config, get_differential_json(), load_json()

### Community 50 - "Lvl1SortValues"
Cohesion: 0.14
Nodes (7): get_moves_for_transforming(), Lvl1SortValues, We move rows as follows: Say the existing rows are…, Get the index moves [(src, dst), ...] to rearrange a sparse list. Eg.:…, GetMovesForTransformingTest, Lvl1SortValuesTest, TestCase

### Community 51 - "._expect"
Cohesion: 0.15
Nodes (7): _distribute_evenly(), _distribute_exponentially(), _get_ideal_column_widths(), _resize_column(), GetIdealColumnWidthsTest, TestCase, ResizeColumnTest

### Community 52 - "as_url"
Cohesion: 0.12
Nodes (5): as_url(), AsFileUrlTest, AsHumanReadableTest, skipIf, TestCase

### Community 53 - "splitscheme"
Cohesion: 0.13
Nodes (6): relpath(), splitscheme(), CreateDirectory, _fs_implements(), FileSystem, StubFS

### Community 54 - "tests/test_release_notes.py"
Cohesion: 0.15
Nodes (14): _candidate_release_dirs(), list_releases(), Pure (no Qt) helpers for the "Release Notes" command…, Renders a loaded release's data as the plain text shown in the viewer…, Candidate release_notes/ locations for `this_file` (this module's own resolved…, Lists the releases in `release_dir`, newest first. Each entry is (version_str,…, render_notes(), _version_tuple() (+6 more)

### Community 56 - "QuicksearchItemRenderer"
Cohesion: 0.17
Nodes (4): QStyledItemDelegate, QuicksearchItemDelegate, QuicksearchItemRenderer, Say we want to highlight chars [2, 3]. The easiest way would be to pass…

### Community 57 - "Executor"
Cohesion: 0.11
Nodes (9): Executor, QObject, Receiver, Sender, Task, QObject, StubApp, TestCase (+1 more)

### Community 58 - "SingleRowMode"
Cohesion: 0.10
Nodes (5): FileListItemDelegate, QStyledItemDelegate, QStyledItemDelegate, SingleRowMode, SingleRowModeDelegate

### Community 59 - "goto.py"
Cohesion: 0.12
Nodes (12): get_core_services(), GoToListener, # TODO: Rename to Visited Locations.json?, _remove_from_visited_paths(), _remove_nonexistent(), _shrink_visited_paths(), unexpand_user(), basename_starts_with() (+4 more)

### Community 60 - "DiffEntry"
Cohesion: 0.17
Nodes (3): ComputeDiff, DiffEntry, N.B.: This implementation requires that there be no duplicate rows!

### Community 61 - "_Delete"
Cohesion: 0.12
Nodes (8): _Delete, DeletePermanently, _describe(), _get_handler_for_archive(), MoveToTrash, Pack, Task, Rename

### Community 63 - ".__init__"
Cohesion: 0.16
Nodes (8): _7zipTaskWithProgress, AddToArchive, _basename(), CopyBetweenArchives, Extract, MoveBetweenArchives, Task, Rename

### Community 64 - "is_mac"
Cohesion: 0.11
Nodes (6): QMacPasteboardMime, MacClipboardFix, Work around QTBUG-61562 on Mac, which can be reproduced as follows: from…, name(), version(), is_mac()

### Community 65 - "ContextMenuProvider"
Cohesion: 0.17
Nodes (6): ContextMenuProvider, _insert_mac_key_symbols(), Suppose the default context menu is * a * b * c1. Further suppose that the user…, sanitize_context_menu(), describe_type(), ordered_set()

### Community 67 - "UniformRowHeights"
Cohesion: 0.16
Nodes (7): DummyModel, QAbstractTableModel, QTableView, The implementation of this method has gone through several iterations: First,…, Performance improvement., The purpose of this model is to let UniformRowHeights "fake" table rows without…, UniformRowHeights

### Community 68 - "change_image_scale"
Cohesion: 0.18
Nodes (8): change_image_scale(), clamp_scale(), reset_image_scale(), ChangeImageScaleTest, ClampScaleTest, _FakeView, TestCase, ResetImageScaleTest

### Community 69 - "ProgressDialog"
Cohesion: 0.13
Nodes (3): QProgressDialog, ProgressDialog, Instead of using @run_in_main_thread on #set_text(...) and #set_progress(...),…

### Community 71 - "QtKeyEvent"
Cohesion: 0.15
Nodes (4): QtKeyEvent, DispatchBindableCommandTest, TestCase, QtKeyEventTest

### Community 72 - "CompositeItemDelegate"
Cohesion: 0.14
Nodes (5): CompositeItemDelegate, MultipleDelegates, QStyledItemDelegate, QTableView, Let a QTableView have multiple ItemDelegates.

### Community 73 - "ShowAllPanes"
Cohesion: 0.16
Nodes (8): _any_pane_hidden(), ShowAllPanes, ShowOnlyActivePane, _FakePane, _FakeWidget, ShowAllPanesTest, ShowOnlyActivePaneTest, _two_pane_window()

### Community 74 - "zip.py"
Cohesion: 0.15
Nodes (10): _get_7zip_args_windows(), _get_7zip_env_encoding_unix(), Popen7Zip, Popen7ZipUnix, Popen7ZipWindows, SevenZipFileSystem, SourceClosingTextIOWrapper, TarFileSystem (+2 more)

### Community 77 - "f"
Cohesion: 0.33
Nodes (4): c(), f(), ModelRecordFilesTest, TestCase

### Community 78 - "8 Essential Additional Rules (must-have)"
Cohesion: 0.12
Nodes (17): 1) Use `pyproject.toml` as the single source of truth, 2) Enforce formatting + linting + type checking in CI, 3) Require type hints on public APIs, 4) Centralize configuration with environment-driven settings, 5) Tests are mandatory, fast, and isolated, 6) Database access uses SQLAlchemy ORM, 7) Use `spec=` with MagicMock to catch interface mismatches, 8 Essential Additional Rules (must-have) (+9 more)

### Community 79 - ".expanduser"
Cohesion: 0.20
Nodes (5): get_user(), GoTo, LocalFileSystem, _get_volumes_url(), get_user()

### Community 81 - "fman_integrationtest/impl/plugins/test_plugin.py"
Cohesion: 0.16
Nodes (6): FormatTracebackTest, TestCase, FailToInstantiateAC, FailToInstantiateDPC, FailToInstantiateDPL, get_resource()

### Community 83 - "ApplicationCommand"
Cohesion: 0.12
Nodes (8): run_in_main_thread, ToggleFullscreen, ApplicationCommand, Help, Minimize, Quit, ReloadPlugins, ZenOfFman

### Community 84 - "is_pardir"
Cohesion: 0.19
Nodes (4): is_pardir(), GetExistingPardirTest, IsPardirTest, TestCase

### Community 86 - "DirectoryPaneListener"
Cohesion: 0.14
Nodes (4): DirectoryPaneListener, ArchiveOpenListener, DragAndDropListener, RememberSortSettings

### Community 87 - "core/os_.py"
Cohesion: 0.20
Nodes (9): _get_os_release_name(), is_arch(), _is_ubuntu(), open_native_file_manager(), open_terminal_in_directory(), _run_app_from_setting(), TestCase, TestStrformatDictValues (+1 more)

### Community 88 - "SplashScreen"
Cohesion: 0.17
Nodes (4): QVBoxLayout, QDialog, QWidget, SplashScreen

### Community 89 - "join"
Cohesion: 0.21
Nodes (6): FindPluginDirsTest, TestCase, join(), find_plugin_dirs(), _list_plugins(), listdir_absolute()

### Community 90 - "SortFilterTableModel"
Cohesion: 0.20
Nodes (4): Implement to give this class the unfiltered, unsorted rows., Return the sort value for the given row. N.B.: row is a Row, not int., Call this after any change in the output of #get_rows()., SortFilterTableModel

### Community 91 - "_TreeCommand"
Cohesion: 0.19
Nodes (5): _get_opposite_pane(), Move, _split(), Symlink, _TreeCommand

### Community 92 - "History"
Cohesion: 0.18
Nodes (4): GoBack, GoForward, History, HistoryListener

### Community 93 - "ShowReleaseNotes"
Cohesion: 0.20
Nodes (5): ShowReleaseNotes, load_release(), Loads the release notes JSON (docs/CREATE_NEW_RELEASE.md schema) for…, TestCase, ShowReleaseNotesTest

### Community 94 - "PaneVideoView"
Cohesion: 0.24
Nodes (3): PaneVideoView, QWidget, save_volume()

### Community 96 - "FileWatcher"
Cohesion: 0.18
Nodes (3): Row, FileWatcher, File

### Community 97 - "clipboard.py"
Cohesion: 0.36
Nodes (13): clear(), _clipboard(), copy_files(), cut_files(), files_were_cut(), _get_extra_copy_cut_data_linux(), get_files(), _get_linux_copy_cut_mime_type() (+5 more)

### Community 99 - "Worker"
Cohesion: 0.19
Nodes (3): Lower priority means "run sooner"., Worker, WorkItem

### Community 100 - "SessionManager"
Cohesion: 0.18
Nodes (3): _decode(), _encode(), SessionManager

### Community 101 - "CursorMovement"
Cohesion: 0.27
Nodes (4): CursorMovement, QTableView, Can be overwritten by subclasses., Can be overwritten by subclasses.

### Community 102 - "LocationBar"
Cohesion: 0.16
Nodes (4): LocationBar, QLineEdit, FilterBar, QFrame

### Community 103 - "test_videoviewer.py"
Cohesion: 0.22
Nodes (5): _FakeSettings, VolumeAndMutePersistenceTest, get_saved_mute(), get_saved_volume(), save_mute()

### Community 105 - "MakeAbsoluteTest"
Cohesion: 0.24
Nodes (3): skipUnless, MakeAbsoluteTest, TestCase

### Community 106 - "fman/impl/util/__init__.py"
Cohesion: 0.28
Nodes (4): ConstructorMixin, EqMixin, MixinBase, ReprMixin

### Community 107 - "DragAndDrop"
Cohesion: 0.24
Nodes (5): DragAndDrop, QAbstractTableModel, List the MIME types used by our drag and drop implementation., from_qurl(), Inverse of as_qurl(...) above.

### Community 108 - "commands/test___init__.py"
Cohesion: 0.24
Nodes (6): _from_human_readable(), ViewFile, _FakeViewFilePane, FromHumanReadableTest, ViewFileTest, _write_temp_file()

### Community 110 - "sanitize_key_bindings"
Cohesion: 0.26
Nodes (3): sanitize_key_bindings(), TestCase, SanitizeKeyBindingsTest

### Community 111 - "normalize"
Cohesion: 0.21
Nodes (3): normalize(), DirnameTest, NormalizeTest

### Community 112 - "ViewFileInOtherPane"
Cohesion: 0.26
Nodes (4): ViewFileInOtherPane, _FakeViewInOtherPane, _FakeWindow, ViewFileInOtherPaneTest

### Community 113 - "GetNavigationStepsTest"
Cohesion: 0.32
Nodes (3): GetNavigationStepsTest, skipIf, TestCase

### Community 115 - "Python Rules (uv)"
Cohesion: 0.18
Nodes (11): Add the `t()` Function, Adding New Languages, Benefits, GUI Framework, Jinja2 Integration, Python Rules (uv), Release Workflow, Template Engine (+3 more)

### Community 116 - "KeyBindings"
Cohesion: 0.20
Nodes (3): KeyBindings, GetContextMenuTest, TestCase

### Community 118 - "build.py"
Cohesion: 0.40
Nodes (9): _commit_version(), _get_suggested_next_version(), post_release(), _prompt_for_next_version(), publish(), release(), _replace_in_json(), _replace_re_group() (+1 more)

### Community 119 - "Creating a New Release"
Cohesion: 0.20
Nodes (9): 1. Version & build number, 2. Release notes directory + `en.json` schema, 3. Translate (mandatory — do not skip), 4.5. Publish to GitHub Releases, 4. Build the release, 5. In-app Release Notes view, Bumping the version, Creating a New Release (+1 more)

### Community 120 - "Text viewer"
Cohesion: 0.20
Nodes (10): Behaviour, Bindable commands, Editing, Implementation, Reload and auto-reload, Text viewer, Two Qt quirks this had to work around, Usage (+2 more)

### Community 121 - "widgets.py"
Cohesion: 0.31
Nodes (3): disable_window_animations_mac(), FilterEventOnce, QObject

### Community 122 - "TestCase"
Cohesion: 0.22
Nodes (4): _find_column_index(), ClampFontSizeTest, FindColumnIndexTest, TestCase

### Community 123 - "_find_extension_start"
Cohesion: 0.29
Nodes (4): _find_extension_start(), get_dest_suggestion(), FindExtensionStartTest, GetDestSuggestionTest

### Community 124 - "is_image"
Cohesion: 0.29
Nodes (4): _is_viewable(), is_image(), IsImageTest, TestCase

### Community 125 - "_OpenInPaneCommand"
Cohesion: 0.24
Nodes (3): OpenInLeftPane, _OpenInPaneCommand, OpenInRightPane

### Community 126 - "ContainsCharsAfterSeparatorTest"
Cohesion: 0.22
Nodes (3): contains_chars_after_separator(), ContainsCharsAfterSeparatorTest, TestCase

### Community 130 - "build_number.py"
Cohesion: 0.38
Nodes (8): _build_file(), decrement(), increment(), label(), Self-contained build-number + release-label helper for the release workflow.…, read_build(), version(), write_build()

### Community 131 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 132 - "Localization"
Cohesion: 0.22
Nodes (9): Container Integration, Controller Helper, Directory Structure, Installation (uv), Localization, Option A (recommended): Add as dependency to the project, Option B: Install into the current environment (without adding to project deps), Python Setup (+1 more)

### Community 133 - "graphify Knowledge Graph (Optional Addon)"
Cohesion: 0.22
Nodes (9): Delegated checks (Codex / DeepSeek), Folder layout (know which is which), graphify Knowledge Graph (Optional Addon), In-tree vendored code — exclude it, scoping alone won't, One-time setup, Refreshing after a code change, Rules to paste into the project's CODING_RULES.md (only if the user opted in), Using the graph (+1 more)

### Community 135 - "ExternalPluginTest"
Cohesion: 0.25
Nodes (3): ExternalPluginTest, PluginTest, TestCase

### Community 140 - "format_time"
Cohesion: 0.33
Nodes (3): FormatTimeTest, TestCase, format_time()

### Community 142 - "AI Workflow Rules (All Languages)"
Cohesion: 0.25
Nodes (8): AI Workflow Rules (All Languages), Bug-Fix Workflow, Definition of Done — restate aloud before implementing, Delegation backends (Codex / DeepSeek), DRY gate (precondition for implementing), Feature / Change Workflow, Optional Addons, Post-implementation DRY audit — paste-in template

### Community 143 - "Key bindings"
Cohesion: 0.25
Nodes (8): Bindable viewer commands, Default bindings — base (all platforms), Files and load order, Key bindings, Linux additions, macOS additions, Viewer-specific bindings, Windows additions

### Community 144 - "Image viewer"
Cohesion: 0.25
Nodes (8): Behaviour, Bindable commands, Image viewer, Implementation, Pan, Usage, Why it works while the file list is hidden, Zoom

### Community 145 - "Video viewer"
Cohesion: 0.25
Nodes (8): Behaviour, Bindable commands, Controls, Implementation, Playback backend, Usage, Video viewer, Why it works while the file list is hidden

### Community 146 - "Prompt"
Cohesion: 0.36
Nodes (4): QInputDialog, Prompt, Most of the code in this otherwise simple class solves the following problem:…, Unfortunately, our double call to paintEvent(...) leads to flickering effects…

### Community 148 - "OpenOrView"
Cohesion: 0.32
Nodes (3): OpenOrView, _FakeOpenOrViewPane, OpenOrViewTest

### Community 153 - "command_for_key_event"
Cohesion: 0.38
Nodes (4): command_for_key_event(), First command in command_names whose configured shortcut matches key_event,…, CommandForKeyEventTest, TestCase

### Community 154 - "release_notes_dir"
Cohesion: 0.33
Nodes (5): first_existing_dir(), Returns the first of `candidates` (an iterable of Path) that exists as a…, Locates the bundled release_notes/ folder. Checked in order: 1. Next to this…, release_notes_dir(), FirstExistingDirTest

### Community 155 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 156 - "Project Setup Scripts"
Cohesion: 0.33
Nodes (6): install.bat, Project Setup Scripts, tools/run_integration_tests.bat, tools/run_tests.bat, update.bat, Usage

### Community 157 - "Show only active pane"
Cohesion: 0.33
Nodes (5): Commands, Implementation, Notes, Show only active pane, Usage

### Community 158 - "Toggle columns"
Cohesion: 0.33
Nodes (5): Commands, Implementation, Notes, Toggle columns, Usage

### Community 159 - "Themes"
Cohesion: 0.33
Nodes (6): How to change fman's colors right now, The wildcard gotcha (why widgets sometimes look "stuck"), Theme.css: files, selectors, and load order, Themes, Two separate color sources — don't confuse them, Writing a new widget that should follow the theme

### Community 165 - "Coding Rules (Pointer)"
Cohesion: 0.40
Nodes (4): Code Analysis, Coding Rules (Pointer), Testing, Version

### Community 166 - "CODING_RULES.md"
Cohesion: 0.40
Nodes (4): Version, Version, Version, Version

### Community 167 - "Open or view"
Cohesion: 0.40
Nodes (5): Commands, Implementation, Notes, Open or view, Usage

### Community 168 - "Pane font size"
Cohesion: 0.40
Nodes (5): Commands, Implementation, Notes, Pane font size, Usage

### Community 169 - "View file"
Cohesion: 0.40
Nodes (5): Commands, Implementation, Notes, Usage, View file

### Community 170 - "Release notes"
Cohesion: 0.40
Nodes (5): Behaviour, Commands, Implementation, Release notes, Usage

### Community 171 - "Window title"
Cohesion: 0.40
Nodes (4): Format, Implementation, Notes, Window title

### Community 174 - "fman_/__init__.py"
Cohesion: 0.80
Nodes (3): raise_error(), run_plugins(), run_plugin()

### Community 175 - "explorer_properties.py"
Cohesion: 0.70
Nodes (4): SHELLEXECUTEINFO, _show_drive_properties(), _show_file_properties(), _show_properties_via_shellexecute()

### Community 176 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 177 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 178 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 179 - "Core"
Cohesion: 0.50
Nodes (3): Core, Examples, Location in your installation directory

### Community 183 - "Inject Collaborators, Don't Fold Dependencies In"
Cohesion: 0.67
Nodes (3): Collapse config-callback swarms into one value object, Inject Collaborators, Don't Fold Dependencies In, Inject services; never instantiate one inside a method

## Knowledge Gaps
- **194 isolated node(s):** `desk.sh script`, `Usage`, `What graphify is for`, `Step 0 - GitHub repos and multi-path merge (only if a URL or several paths)`, `Step 1 - Ensure graphify is installed` (+189 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **48 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FileSystem` connect `FileSystem` to `MoveFiles`, `SortedFileSystemModelAT`, `core/commands/__init__.py`, `QuicksearchItem`, `plugin.py`, `Configure`, `StubUI`, `OpenOrView`, `DrivesFileSystem`, `LocalFileSystem`, `CommandPalette`, `Column`, `PaneCommandRegistry`, `Plugin`, `normalize`, `Cache`, `_7ZipFileSystem`, `StubFileSystem`, `_7zip`, `CachedIterator`, `splitscheme`, `_Delete`, `.__init__`, `ExternalPlugin`, `ShowAllPanes`, `zip.py`, `ApplicationCommand`, `DirectoryPaneListener`, `_TreeCommand`, `History`, `commands/test___init__.py`, `ViewFileInOtherPane`, `FileSystemWrapperTest`, `_OpenInPaneCommand`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Why does `DevelopmentApplicationContext` connect `DevelopmentApplicationContext` to `SortedFileSystemModelAT`, `PluginErrorHandler`, `Tour`, `plugin.py`, `MotherFileSystem`, `CommandCallback`, `UsageHelper`, `ServerBackend`, `NonexistentShortcutHandler`, `Column`, `PaneCommandRegistry`, `application_context.py`, `fman/__init__.py`, `Tutorial`, `User`, `fman/impl/view/__init__.py`, `Config`, `MainWindow`, `is_mac`, `ContextMenuProvider`, `ExternalPlugin`, `PluginSupport`, `SplashScreen`, `join`, `Controller`, `SessionManager`, `KeyBindings`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `splitscheme()` connect `splitscheme` to `MoveFiles`, `as_human_readable`, `textviewer.py`, `SortedFileSystemModelAT`, `core/commands/__init__.py`, `Configure`, `MotherFileSystem`, `DrivesFileSystem`, `LocalFileSystem`, `basename`, `application_context.py`, `SortedFileSystemModel`, `normalize`, `._create_empty_zip`, `Path`, `dirname`, `Tutorial`, `as_url`, `goto.py`, `_Delete`, `FileTreeOperation`, `.__init__`, `f`, `DirectoryPaneListener`, `join`, `_TreeCommand`, `clipboard.py`, `commands/test___init__.py`, `normalize`, `widgets.py`, `_find_extension_start`, `is_image`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 153 inferred relationships involving `FileSystem` (e.g. with `CommandRaisingError` and `ListenerRaisingError`) actually correct?**
  _`FileSystem` has 153 INFERRED edges - model-reasoned connections that need verification._
- **Are the 98 inferred relationships involving `MoveFiles` (e.g. with `About` and `ArchiveOpenListener`) actually correct?**
  _`MoveFiles` has 98 INFERRED edges - model-reasoned connections that need verification._
- **Are the 98 inferred relationships involving `CopyFiles` (e.g. with `About` and `ArchiveOpenListener`) actually correct?**
  _`CopyFiles` has 98 INFERRED edges - model-reasoned connections that need verification._
- **Are the 94 inferred relationships involving `GitHubRepo` (e.g. with `About` and `ArchiveOpenListener`) actually correct?**
  _`GitHubRepo` has 94 INFERRED edges - model-reasoned connections that need verification._