# Window title

The fman window title shows both panes' current paths, kept in sync as either
pane navigates.

## Format

```
fman - file manager - <left pane path> | <right pane path>
```

Example:

```
fman - file manager - C:\test | D:\GIT\BenjaminKobjolke\fman\debug
```

- A fixed `fman - file manager` prefix.
- Pane paths in **left, right** order (matches pane order everywhere else in
  fman, e.g. `window.get_panes()`), separated by ` | `.
- A pane whose path can't be rendered (e.g. `null://`) is skipped rather than
  shown as garbage; with zero renderable panes the title falls back to just
  the prefix.
- Updates live: navigating either pane (open a folder, go up, jump via the
  location bar, etc.) refreshes the whole title, not just that pane's segment.

## Notes

- This replaces the static title set by the core app (`fman`) once the main
  window is shown. There is no registration marker to fold in: this fork has
  no licensing (see `docs/PURCHASING.md`).

## Implementation

- `src/main/resources/base/Plugins/Core/core/commands/__init__.py` —
  `UpdateWindowTitle` (`DirectoryPaneListener`). Sets the title once on
  startup and again on every `on_path_changed`, mirroring the existing
  `InitHiddenFilesFilter` / `InitPaneFontSize` startup-listener pattern.
- `_format_window_title(paths)` is the pure string builder (prefix + join),
  kept separate from pane/Qt access so it's unit-testable without a running
  application. `_path_for_title(pane)` converts a pane's URL
  (`pane.get_path()`) to a human-readable path via `as_human_readable(...)`,
  swallowing any conversion error as a blank/skipped segment.
- `_refresh_window_title(window)` reads all panes via `window.get_panes()`
  and calls `window._widget.setWindowTitle(...)`. `DirectoryPaneListener`
  callbacks run off the Qt main thread
  (`ListenerWrapper._notify_listener_in_thread`), so this function is
  decorated with `@run_in_main_thread` — the same pattern already used by
  `ResetPaneFontSize` and `ShowOnlyActivePane`/`ShowAllPanes` in this file.
- `src/main/resources/base/Plugins/Core/core/tests/commands/test___init__.py`
  — `FormatWindowTitleTest` covers the pure title-building logic (no paths,
  blank paths skipped, one path, two paths).
