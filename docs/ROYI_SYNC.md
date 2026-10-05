# Royi sync ledger

Which changes from the RoyiFileManager fork have been ported into this fork.
Maintained by the `royi-sync` skill (`.claude/skills/royi-sync/SKILL.md`).

Source: https://github.com/RoyiAvital/RoyiFileManager (local: `D:\GIT\GitHub\RoyiFileManager`)
Last reviewed: v0.11.0 (cc5824f)

The two repositories share no git history, so nothing can be merged or
cherry-picked — every row is a manual re-implementation. Rows follow the
bullets of Royi's `CHANGELOG.md`, newest version first.

Status: `pending` (not looked at yet), `ported`, `skipped` (with reason).

| Version | Change | Status | Note |
|---------|--------|--------|------|
| 0.11.0 | Everything Search plug-in (Ctrl+E), database folder manager | pending | bundles Everything portable binary |
| 0.11.0 | Build auto-provisions hash-verified Everything portable files | pending | belongs to the plug-in above |
| 0.10.3 | ChecksumFiles plug-in (generate / verify checksum files) | pending | needs `show_table` (0.4.0), BLAKE3 dependency |
| 0.10.3 | `get_background_menu` callback in `fman.ui.show_table` | pending | needs `show_table` (0.4.0) |
| 0.10.3 | Performance retest report | skipped | measurement of his builds, no code |
| 0.10.2 | Faster readback of selected file lists (36x on 200k files) | pending | |
| 0.10.2 | Simplified clipboard, Explorer and Recycle Bin command handling | pending | |
| 0.10.2 | QuickView Find field forwards modified Enter shortcuts | pending | needs QuickView (0.8.0 / 0.10.0) |
| 0.10.2 | Compare directories reports selected visible differences | pending | |
| 0.10.2 | Pack at drive root suggests `C.zip` instead of `C:.zip` | ported | 2026-10-03 — `core/commands/pack.py` (`_suggest_archive_name`), `core/tests/commands/test_pack.py` |
| 0.10.2 | Delete continuation prompts use the task dialog, explicit Yes default | pending | |
| 0.10.1 | Removed macOS/Linux runtime branches | skipped | this fork stays cross-platform |
| 0.10.1 | Removed GitHub plug-in installer | skipped | this fork keeps it (`docs/INSTALL_PLUGINS.md`) |
| 0.10.1 | Removed telemetry / event history | pending | |
| 0.10.1 | Removed legacy Column `get_str` / `get_sort_value` | skipped | only valid on snapshot architecture (0.9.0) |
| 0.10.1 | Renamed "Show processes" to "Show OS' processes" | pending | needs ProcessPane (0.6.0) |
| 0.10.1 | Less unknown-identity checking when reconciling listings | pending | snapshot architecture (0.9.0) |
| 0.10.1 | Arrow-key suggestions offer local bindings; removed "Other" feedback field | pending | |
| 0.10.1 | Drive-label lookup moved to the filesystem scanner | pending | snapshot architecture (0.9.0) |
| 0.10.1 | Optional date edits commit on Enter / focus loss | pending | needs Find files panel (0.7.0) |
| 0.10.1 | Documentation updates | skipped | his docs |
| 0.10.0 | QuickView previews text, Markdown and source code | pending | needs QuickView (0.8.0); this fork has own text viewer |
| 0.9.3 | Less redundant pane column sizing, icon-key and status checks | pending | |
| 0.9.3 | Find reuses name/path normalization, streams ranked candidates | pending | needs SearchFileFuzzy (0.2.0) |
| 0.9.3 | Command Center avoids repeated lowercase conversions | pending | |
| 0.9.3 | Performance report | skipped | no code |
| 0.9.2 | File operations no longer traverse junction targets; hardlink copies refused | pending | data safety |
| 0.9.2 | Staged copies, Windows overwrite preserves DACLs and streams | pending | data safety |
| 0.9.2 | Atomic session/dialog saves, linked settings files refused | pending | data safety |
| 0.9.2 | Worker/process startup failures release capacity and clean up | pending | |
| 0.9.2 | Folder-access failures recover through navigation; UTF-8/BOM config | pending | |
| 0.9.2 | Natural sort handles long numeric runs and Unicode digits; Go To keeps offline history | pending | |
| 0.9.2 | Resource cache hits avoid allocation; unchanged sort prefs skip disk writes | pending | |
| 0.9.2 | `FMAN_VERSION` replaced by `APP_VERSION` | skipped | rebrand |
| 0.9.2 | About dialog shows product version and links | skipped | rebrand |
| 0.9.2 | Removed obsolete pre-snapshot row loading | skipped | snapshot architecture cleanup |
| 0.9.2 | Application identity derived from `app_name` | skipped | rebrand / packaging |
| 0.9.2 | Documentation and performance report | skipped | his docs, no code |
| 0.9.1 | QuickView "Copy Image" button | pending | needs QuickView (0.8.0) |
| 0.9.0 | Snapshot pane architecture (immutable snapshots, one virtual model) | pending | very large; breaks filesystem/column/filter API |
| 0.9.0 | Filter Bar projections off the Qt thread | pending | part of snapshot architecture |
| 0.9.0 | Lazy icons and cell text through bounded caches | pending | part of snapshot architecture |
| 0.9.0 | Performance test suite (`python build.py measure`) | pending | |
| 0.9.0 | Synthetic benchmark fixtures | pending | belongs to the suite above |
| 0.9.0 | Native Filter Bar / Find / QuickView benchmark workloads | pending | belongs to the suite above |
| 0.9.0 | Escape in search panels returns focus to last active pane | pending | needs search panels (0.4.0 / 0.7.0) |
| 0.9.0 | Archive panes include deeply implied directories | pending | |
| 0.8.1 | Nested plug-in settings merge recursively (upstream `f3e48d2`) | ported | `fman/impl/plugins/config.py`, `test_config.py` |
| 0.8.1 | Reuse Windows directory entries' hidden attributes | pending | |
| 0.8.0 | Image QuickView (Ctrl+Q) | pending | this fork has own image viewer |
| 0.8.0 | `tinycss` replaced by `tinycss2` | pending | new dependency |
| 0.8.0 | No row-height recalculation on metadata updates in large folders | ported | 2026-10-05 — `fman/impl/view/__init__.py` (vertical header `Fixed`), `view/uniform_row_heights.py` (`setDefaultSectionSize`; also on icon size change, which is fork-only), `fman_unittest/impl/view/uniform_row_heights_test.py`; measured at 37k rows: 0.33 s -> 0 s of GUI thread per background-load commit |
| 0.8.0 | Qt tests use nonblocking completion notification | pending | may relate to the known test hang; needs his main-thread `QApplication` test runner (`QtIT.run`, `qt_runner`) first |
| 0.7.1 | File / folder comparator wizards, Compare files / folders | pending | |
| 0.7.1 | Find Files cancel reports Stopped, not Error | pending | needs Find files panel (0.7.0) |
| 0.7.1 | Find Files counts "entries" rather than "files" | pending | needs Find files panel (0.7.0) |
| 0.7.0 | Find files with fd panel (Shift+F7) | pending | bundles fd binary, needs `show_panel` (0.4.0) |
| 0.7.0 | `fman.ui` dropdown, date/integer fields, section dividers | pending | needs `show_panel` (0.4.0) |
| 0.7.0 | EmEditor preset for text editor / viewer | pending | needs editor wizards (0.5.1) |
| 0.7.0 | Command renames: Find files, Favorites manager, Search files, New file | pending | |
| 0.7.0 | Minimum window size 960 x 600 | pending | |
| 0.6.4 | CudaText preset arguments | pending | needs editor wizards (0.5.1) |
| 0.6.3 | Notepad 4 preset; Notepad++ preset arguments | pending | needs editor wizards (0.5.1) |
| 0.6.2 | Notepad 4 preset | pending | same as 0.6.3 row |
| 0.6.1 | Modified date and size beneath fuzzy search results | pending | needs SearchFileFuzzy (0.2.0) |
| 0.6.0 | ProcessPane plug-in (process list, F8 terminate) | pending | |
| 0.6.0 | Fuzzy search supports fzf extended query operators | pending | needs SearchFileFuzzy (0.2.0) |
| 0.5.1 | External text viewer / editor wizards (F3 / F4) | pending | |
| 0.5.1 | About shows product version | skipped | rebrand |
| 0.5.0 | Pane filter syntax (`?`, classes, anchors, negation) and matched/total counts | pending | |
| 0.5.0 | Search File Content lists files by name when content pattern is empty | pending | needs Search files (0.4.0) |
| 0.5.0 | Content Glob matches anywhere in a line | pending | needs Search files (0.4.0) |
| 0.5.0 | Closing a Table after navigation leaves target file current | pending | needs `show_table` (0.4.0) |
| 0.5.0 | TextField labels show input tooltips | pending | needs `show_panel` (0.4.0) |
| 0.4.4 | Directory totals in the Size column (Ctrl+Shift+D) | pending | |
| 0.4.4 | Column widths restored by name across optional-column changes | pending | |
| 0.4.4 | Ignore queued pane-reload results after model shutdown | pending | |
| 0.4.3 | Unpack archive command | pending | check against `docs/ARCHIVES.md` |
| 0.4.2 | Archive extraction progress and cancel | pending | this fork has own `-bsp1` progress work |
| 0.4.2 | Move out of / between archives verifies before deleting source | pending | data safety |
| 0.4.2 | Failed or canceled extraction cannot trigger source deletion | pending | data safety |
| 0.4.2 | Archive-to-archive Move no longer deletes source before packing succeeds | pending | data safety |
| 0.4.2 | Windows directory publication refuses late destination conflicts | pending | |
| 0.4.2 | Build retries transient 7-Zip download failures | skipped | his build pipeline |
| 0.4.1 | Command Palette pins three most recent commands | pending | this fork has own palette work |
| 0.4.1 | `load_json(..., preserve_on_reload=True)` | pending | |
| 0.4.1 | Search File Content pane indicators | pending | needs Search files (0.4.0) |
| 0.4.0 | Search File Content with ripgrep (Alt+F7) | pending | bundles ripgrep binary |
| 0.4.0 | Table UI component `fman.ui.show_table` | pending | prerequisite for many later rows |
| 0.4.0 | Docked panel UI component `fman.ui.show_panel` | pending | prerequisite for many later rows |
| 0.4.0 | `DirectoryPane.on_path_changed` subscriptions | pending | |
| 0.4.0 | Fuzzy matching prefers contiguous matches | pending | |
| 0.4.0 | Test suite timing issue with misleading permission traceback | pending | |
| 0.3.1 | Calculate File Hash (Ctrl+H) and algorithm picker | pending | needs `OutputTextBox` |
| 0.3.1 | `fman.ui.OutputTextBox` | pending | |
| 0.3.1 | Startup status uses application version | skipped | rebrand |
| 0.3.0 | Vector SVG application icon | skipped | his branding |
| 0.3.0 | Reusable `fman.ui` components (QuickList, bottom panel, toggles, settings bindings) | pending | |
| 0.3.0 | Public host-owned UI construction, pane tool windows, shared matchers | pending | |
| 0.3.0 | Favorites Manager (Ctrl+B) | skipped | covered by own external plug-in FMAN-Favorites (README "Plugins") |
| 0.2.2 | Extended Status Bar fixes (64-bit summaries, background, Active marker) | pending | needs extended status bar (0.2.0) |
| 0.2.1 | ZIP tests generate their fixture, accept fractional 7-Zip timestamps | pending | |
| 0.2.1 | Windows archive operations decode Unicode 7-Zip output consistently | pending | |
| 0.2.1 | Release builds materialize LFS icon | skipped | his build pipeline |
| 0.2.0 | SearchFileFuzzy plug-in (current-folder and recursive fuzzy search) | pending | |
| 0.2.0 | Optional extended status bar (Ctrl+S) | pending | this fork has own status bar work (`docs/STATUSBAR.md`) |
| 0.2.0 | Sync Pane Location command | pending | |
| 0.2.0 | Favorites plug-in (Ctrl+B) | skipped | covered by own external plug-in FMAN-Favorites (README "Plugins") |
| 0.2.0 | Ctrl+N creates an empty file without opening an editor | pending | |
| 0.2.0 | README, provenance metadata, release-build hardening | skipped | his repo housekeeping |
| 0.1.0 | Portable distribution, conda workflow, PyInstaller packaging, 7-Zip retrieval | skipped | his packaging |
| 0.1.0 | Rebrand, local `fbs_runtime`, removed non-Windows and licensing code | skipped | his fork identity |
| 0.1.0 | Windows tests that do not need symlink privileges | pending | |
| 0.1.0 | Faster sorting of large directories and pane resizing | pending | includes the later "painting failed after resize" fix |
| 0.1.0 | Faster natural name sorting | pending | |
| 0.1.0 | Larger local file copy buffer | pending | |
| 0.1.0 | Skip unused Gnome icon provider detection on Windows | pending | |
| 0.1.0 | F1 opens searchable keyboard shortcut guide | pending | this fork has own keybinding docs / palette |
| 0.1.0 | 1280x800 default window, Reset Window Geometry command | pending | |
| 0.1.0 | Application context lifetime fix (native Qt startup crashes) | pending | |
| 0.1.0 | Worker / file-watcher / QApplication shutdown races in tests | ported | 2026-10-03 — `fman/impl/model/model.py` (`shutdown` never ran `_shutdown_async`), `worker.py`, `file_watcher.py`, `fman_integrationtest/test_qt.py`; effect on the known test hang not measured |
| 0.1.0 | `Worker.submit` forwards keyword arguments | ported | 2026-10-03 — `fman/impl/model/worker.py`, `fman_unittest/impl/model/test_worker.py` |
| 0.1.0 | `WorkItem.__eq__` compared tuples incorrectly | ported | 2026-10-03 — same files as the row above |
| 0.1.0 | "Sort value is not loaded" after changing sort column then relaxing filter | ported | 2026-10-03 — `fman/impl/model/model.py` (`sort`), `fman_unittest/impl/model/test_model.py` |
| 0.1.0 | Move over existing file duplicated its name in cached listing | ported | 2026-10-03 — `fman/impl/plugins/mother_fs.py` (`_add_to_parent`), `test_mother_fs.py` |
| 0.1.0 | Duplicate additions to lazy plug-in directory listings left stale entries | ported | 2026-10-03 — `mother_fs.py` (`CachedIterator._record`); same change as the row above |
| 0.1.0 | Frozen Qt dependency collection, locked-build detection, title bar icon | skipped | his packaging |
