# Command palette

fman's command palette is a fuzzy-search picker for running any command by
name instead of hunting for a key binding. Type part of a command's name (or
one of its hidden keywords, below), pick from the filtered list, press Enter.

## The global command palette

- **Open it:** `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS) —
  the `command_palette` command (see [`docs/KEYBINDINGS.md`](KEYBINDINGS.md)).
- **Search:** matching is fuzzy — the typed characters just have to appear in
  order (`core/quicksearch_matchers.py`), so `vf` finds *View file*. Words
  after a space match on word boundaries first, then anywhere.
- **Word order doesn't matter:** space-separated words are also matched in any
  order, so `panes show` finds *Show all panes* just like `show panes` does.
  In-order and word-boundary matches still rank first; any-order matches fall
  to the bottom of the list.
- **Shortcut hints:** each entry shows the key it's currently bound to (if
  any), read live from the merged `Key Bindings.json` — rebind a command and
  the hint updates.
- **Remembers your last pick:** reopening the palette pre-selects the command
  you last ran, so repeating an action is Open → Enter.
- **Scope:** lists every command visible for the active pane plus global
  application commands. Only commands the pane marks visible show up.

Commands worth knowing about that have no default key binding, so the
palette is the only way to reach them:

- **Select theme** — switch fman's colors, applied immediately. See
  [`docs/functions/select-theme.md`](functions/select-theme.md).
- **Set window opacity** — make the window see-through, or hand the choice
  back to the theme. See
  [`docs/functions/window-opacity.md`](functions/window-opacity.md).
- **Center window** — puts fman back in the middle of the screen it is
  already on (also found by *center window on screen*, *move window to
  center*, *middle*). Centered within the *available* area, so the taskbar
  doesn't push it off-center, and on two monitors it stays on the monitor it
  was on. Bind it with
  `{ "keys": ["Ctrl+Alt+C"], "command": "center_window" }` — see
  [`docs/KEYBINDINGS.md`](KEYBINDINGS.md).

It searches the **file-list** widget only. While an in-pane viewer is open,
the file list is hidden, so the global palette can't reach the viewer — that's
why viewers ship their own.

## Hidden search keywords

A command is also findable by words that are **not** in its name. They live
in `Command Keywords.json` — a flat map of command name to search terms — and
are never displayed: typing *transparency* selects the row that still reads
**Set window opacity**.

```json
{
    "set_window_opacity": ["transparency", "opacity", "alpha"],
    "pack": ["zip", "7z", "tar", "compress"],
    "video_mute": ["sound", "volume", "audio"]
}
```

- **Exact matches come first.** Typing a command's whole name, or a whole
  keyword, puts that row at the very top - which is why *exit* offers
  **Quit** before *Extract to opposite*, whose name happens to contain
  `e`, `x`, `i`, `t` in that order.
- **Otherwise names match first.** A row found by its real name ranks above
  one found only by a keyword, and only the name match highlights the typed
  characters — a keyword hit has nothing in the title to underline.
- **The keys are command names**, the same ones
  [`docs/KEYBINDINGS.md`](KEYBINDINGS.md) uses — viewer pseudo-commands
  (`video_mute`, `viewer_next_file`) included, so the viewer palettes below
  read the same file.
- **Add your own** in `%APPDATA%/fman/Plugins/User/Settings/Command Keywords.json`
  (equivalent per-OS `Plugins/User/Settings/` folder elsewhere), next to your
  `Key Bindings (<OS>).json`. Unlike key bindings, a command you name there
  **replaces** fman's list for that command, so repeat the built-in terms you
  want to keep. Every other command is untouched.
- Terms are lowercase, and matched the same fuzzy way names are.

## Viewers have their own palettes

Each in-pane [file viewer](viewers/FILE_VIEWERS.md) has a **separate,
viewer-scoped command palette**, also on **`Ctrl+Shift+P`**, but reaching
different commands — the ones that make sense for what you're viewing:

| Viewer | Palette entries (summary) |
|--------|----------------------------|
| [Text viewer](views/TEXT_VIEWER.md#editing) | Exit, Edit file, Save / Save as…, Reload / Revert, auto-reload & tail toggles, font-size zoom, Next/Previous file, Advance-same-type toggle |
| [Image viewer](views/IMAGE_VIEWER.md#zoom) | Zoom in/out, Fit to window, Actual size (100%), Reset zoom, Next/Previous file, Advance-same-type toggle, Exit |
| [Video viewer](views/VIDEO_VIEWER.md#controls) | Play/Pause, Restart, Mute/Unmute, Reset volume, Next/Previous file, Advance-same-type toggle, Exit |

Notes:

- The viewer palette is built on the same `show_quicksearch` API as the
  global one, so it fuzzy-searches and shows shortcut hints the same way.
- The entry set changes with context — e.g. the text viewer shows different
  entries in view mode vs. edit mode.
- These are **viewer-only pseudo-commands**, not global `DirectoryPaneCommand`s.
  Bind your own keys to them in a **separate** `Viewer Key Bindings (<OS>).json`
  file — see [`docs/KEYBINDINGS.md`](KEYBINDINGS.md#viewer-specific-bindings).
