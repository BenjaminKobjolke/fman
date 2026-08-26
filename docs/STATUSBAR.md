# Status bar

The strip along the bottom of fman's window. It shows one line of text at a
time — the last message fman or a plugin had to say — and nothing else. It can
be turned off from the [command palette](COMMAND_PALLETTE.md), and stays off
across restarts.

## What it shows

There is a single message slot, left-aligned. Whatever wrote last wins.

| When | Message |
|------|---------|
| Startup | `v1.7.8 ready.` — or `Updated to v1.7.8. Changelog` after a version change, where *Changelog* is a clickable link |
| Copy / cut to clipboard | `Copying foo.txt`, `Cutting foo.txt and 3 other files`, `Copied C:\dir\foo.txt to the clipboard` |
| Reloading plugins | `Reloaded 2 plugins.` |
| Saving in the [text viewer](views/TEXT_VIEWER.md#editing) | `Saved`, `Saved as <path>` |
| Auto-reload / tail toggles | `Auto-reload on`, `Tail mode on`, `Auto-reload off`, `File changed on disk (not reloaded)` |
| [Viewer navigation](viewers/FILE_VIEWERS.md) | `Advance only for same type: on`, `No further file to view` |
| Long-running work | a "doing X…" line for as long as the work runs, then cleared |
| Nothing recent | `Ready.` |

Messages either sit there until something replaces them, or carry a timeout
after which the bar falls back to `Ready.` — 2–5 seconds for the routine ones,
longer for hints.

A message may contain HTML links (the changelog one does); they open in the
external browser.

## Turning it off

Press **`Ctrl+Shift+P`** and run **"Toggle status bar"**. The bar disappears
immediately and the panes grow into the row it occupied — the window keeps its
size on screen. Running the command again brings it back.

| Command name        | Palette label     | Platform | Default key binding |
|----------------------|--------------------|-----------|----------------------|
| `toggle_status_bar`  | Toggle status bar  | all       | none (palette only)  |

*statusbar*, *hide status bar*, *message bar*, *bottom bar* and *chrome* also
find the row — hidden keywords, so it still reads "Toggle status bar". See
[the command palette](COMMAND_PALLETTE.md#hidden-search-keywords).

Bind it to a key like any other command
(see [`docs/KEYBINDINGS.md`](KEYBINDINGS.md)):

```json
{ "keys": ["Ctrl+Alt+S"], "command": "toggle_status_bar" }
```

### Notes

- **Messages are not lost, just not drawn.** fman and plugins keep calling
  `show_status_message(...)` while the bar is hidden; the text is set on a
  widget nobody can see, and the latest one is there when you bring the bar
  back. Nothing errors, nothing queues up.
- **Hiding it is not the same as hiding the title bar.** The status bar is an
  ordinary child widget, so switching it off does not recreate the window and
  has none of the frameless-window caveats — the window stays draggable and
  closable. See [Toggle title bar](functions/window-bars.md).
- **The state survives a restart without a flash**, applied before the window
  is first shown, the same way the title bar and
  [window opacity](functions/window-opacity.md) are.

## Theming

The bar is styled through two tokens (see [`docs/THEMES.md`](THEMES.md)):

| Token                  | What it paints                                     |
|-------------------------|-----------------------------------------------------|
| `statusbar_bg_top`      | Top of the vertical background gradient             |
| `statusbar_bg_bottom`   | Bottom of it — falls back to `statusbar_bg_top`, so a flat bar means naming only the one token |

The text colour is `bright_fg` and the line above the bar is `border`; both
are shared with the rest of the chrome rather than being status-bar-specific.
Its font size is set in `Theme.css` under the `.statusbar` selector (8pt by
default, 11pt on macOS), which maps to `QStatusBar, QStatusBar QLabel`.

## Where it lives

- The widget: `fman/impl/widgets.py` — `MainWindow.__init__` builds the
  `QStatusBar` and the `QLabel` inside it (`setOpenExternalLinks(True)` is what
  makes the changelog link clickable, `setSizeGripEnabled(False)` removes the
  resize grip), plus `show_status_message` / `clear_status_message` and the
  single-shot `QTimer` behind `timeout_secs`
- The plugin API: `fman.show_status_message(text, timeout_secs=None)` and
  `fman.clear_status_message()` — see [`docs/PLUGINS_API.md`](PLUGINS_API.md).
  `core.commands.StatusMessage` is a context manager wrapping the pair for
  "show while this runs"
- The startup message: `fman/impl/session.py`
- Toggle command: `fman/impl/plugins/builtin.py` (`ToggleStatusBar`), beside
  `ToggleTitleBar`
- Show/hide on the widget: `MainWindow.set_status_bar_visible`
- State and persistence: `fman/impl/window_chrome.py` (`WindowChrome`), saved
  as `status_bar_visible` in `%APPDATA%/fman/Local/Settings.json`. The key is
  only written while the bar is hidden; a visible bar is the absence of the key
- Styling: `src/main/resources/base/styles.qss` (gradient, border, text
  colour), `src/main/resources/windows/os_styles.qss` (`min-height`), and
  `Plugins/Core/Theme.css` / `Theme (Mac).css` (font size)
