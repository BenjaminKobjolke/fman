# Command palette

fman's command palette is a fuzzy-search picker for running any command by
name instead of hunting for a key binding. Type part of a command's name (or
one of its aliases), pick from the filtered list, press Enter.

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

It searches the **file-list** widget only. While an in-pane viewer is open,
the file list is hidden, so the global palette can't reach the viewer — that's
why viewers ship their own.

## Viewers have their own palettes

Each in-pane [file viewer](viewers/FILE_VIEWERS.md) has a **separate,
viewer-scoped command palette**, also on **`Ctrl+Shift+P`**, but reaching
different commands — the ones that make sense for what you're viewing:

| Viewer | Palette entries (summary) |
|--------|----------------------------|
| [Text viewer](views/TEXT_VIEWER.md#editing) | Exit, Edit file, Save / Save as…, Reload / Revert, auto-reload & tail toggles, font-size zoom |
| [Image viewer](views/IMAGE_VIEWER.md#zoom) | Zoom in/out, Fit to window, Actual size (100%), Reset zoom, Exit |
| [Video viewer](views/VIDEO_VIEWER.md#controls) | Play/Pause, Restart, Mute/Unmute, Reset volume, Exit |

Notes:

- The viewer palette is built on the same `show_quicksearch` API as the
  global one, so it fuzzy-searches and shows shortcut hints the same way.
- The entry set changes with context — e.g. the text viewer shows different
  entries in view mode vs. edit mode.
- These are **viewer-only pseudo-commands**, not global `DirectoryPaneCommand`s.
  Bind your own keys to them in a **separate** `Viewer Key Bindings (<OS>).json`
  file — see [`docs/KEYBINDINGS.md`](KEYBINDINGS.md#viewer-specific-bindings).
