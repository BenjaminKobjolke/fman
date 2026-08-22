# Pane font size

Command palette entries (plus two default key bindings) to zoom the font size
of both file panes in and out on the fly, and to reset it back to the theme's
original size.

## Usage

1. Press **Alt+Up** to make the text in both panes larger, **Alt+Down** to
   make it smaller. Both panes always change together.
2. Open the command palette and search "font size" to run the same actions,
   plus **Reset font size** (palette-only, no default key binding).
3. The chosen size is remembered — it survives restarting fman.

## Commands

| Command name               | Palette label / aliases                              | Default key binding |
|-----------------------------|--------------------------------------------------------|----------------------|
| `increase_pane_font_size`   | Increase font size, Zoom in, Larger pane font           | `Alt+Up`             |
| `decrease_pane_font_size`   | Decrease font size, Zoom out, Smaller pane font         | `Alt+Down`           |
| `reset_pane_font_size`      | Reset font size, Default font size                      | none (palette only)  |

These can be rebound in `Key Bindings.json` like any other command, e.g.:

```json
{ "keys": ["Ctrl+0"], "command": "reset_pane_font_size" }
```

## Notes

- The font size is stored in `Core Settings.json` under the `pane_font_size`
  key. Running **Reset font size** removes that key entirely rather than
  writing back a hard-coded default.
- Only the two file-list panes are affected — the status bar, location bar,
  column headers, and command palette keep their own font size.
- **Respects a custom theme.** If you have your own
  `Theme.css` (e.g. `%APPDATA%/fman/Plugins/User/Settings/Theme.css` on
  Windows) that sets a different base `font-size`, the first zoom press steps
  from *that* size, not from fman's built-in default. Resetting removes the
  override completely, so the pane goes back to rendering your theme exactly
  as authored.
- Font size is clamped between 6pt and 40pt; repeatedly zooming past either
  end has no further effect.
- **`go_up` moved to Ctrl+Up on Windows and Linux.** Alt+Up was previously
  `go_up` (go to parent directory) on those two platforms. To free it for
  this feature, `go_up` is now bound to **Ctrl+Up** there instead. On Mac,
  `go_up` was already `Cmd+Up`, so nothing changed. `go_up` is still also
  available on **Backspace** on every platform.

## Implementation

- `src/main/resources/base/Plugins/Core/core/commands/__init__.py` —
  `IncreasePaneFontSize`, `DecreasePaneFontSize`, `ResetPaneFontSize`
  (`DirectoryPaneCommand` subclasses), plus `InitPaneFontSize`
  (`DirectoryPaneListener`) which re-applies a saved size when fman starts
  (mirrors the existing `InitHiddenFilesFilter` pattern).
- The font is changed by setting a **widget-local QSS stylesheet** directly on
  each pane's file view: `FileListView { font-size: Npt; }`. This is applied
  via `pane._widget._file_view.setStyleSheet(...)`. A type-selector rule set
  locally on the widget beats both the app-wide `* { font-size }` rule from
  `Theme.css` and any user theme that also relies on that same `*` selector —
  so zooming works regardless of which theme is active.
- The starting size (before any zoom has ever been applied) is read directly
  off the live pane via `QFontInfo(view.font()).pointSize()`, so it reflects
  whatever theme is currently loaded rather than a hard-coded constant.
- `src/main/resources/base/Plugins/Core/Key Bindings.json` — the two default
  bindings above.
- `src/main/resources/base/Plugins/Core/Key Bindings (Windows).json` and
  `Key Bindings (Linux).json` — `go_up` rebound from `Alt+Up` to `Ctrl+Up`.
  `Key Bindings (Mac).json` was not touched (`go_up` was already `Cmd+Up`).
- **Why the platform files had to change too:** fman loads the base
  `Key Bindings.json` first, then the platform-specific file, and the
  platform file's bindings are checked *before* the base file's — first match
  wins (`Controller.handle_shortcut`, `controller.py:35-44`). So a base-file
  binding for a key a platform file already claims is silently shadowed on
  that platform; adding Alt+Up in the base file alone would not have worked
  on Windows/Linux.
- `src/main/resources/base/Plugins/Core/core/tests/commands/test___init__.py`
  — `ClampFontSizeTest` covers the pure step/clamp logic.
