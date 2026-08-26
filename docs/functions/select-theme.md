# Select theme

Switches fman's color theme from the [command palette](../COMMAND_PALLETTE.md),
applying it immediately — no restart.

## Usage

1. Press **`Ctrl+Shift+P`** and run **"Select theme"**.
2. A quicksearch list shows every installed theme. The active one is
   preselected and marked `current`. Type to fuzzy-filter, like any other
   palette list.
3. Pick one (Enter, or click). The panes, header, status bar, location bar,
   dialogs and the palette itself recolor right away, and the choice is
   remembered across restarts.

A file viewer that is **already open** (text, image, video) keeps its old
colors until you close and reopen it — those viewers copy the pane's colors
when they open. Context menus on Windows and macOS stay native-looking under
every theme.

## Commands

| Command name   | Palette label | Default key binding |
|----------------|----------------|---------------------|
| `select_theme` | Select theme   | none (palette only) |

*Change theme*, *color scheme*, *colors*, *dark mode* and *skin* find it too —
they are hidden keywords, so the row still reads "Select theme". See
[the command palette](../COMMAND_PALLETTE.md#hidden-search-keywords).

Bind it to a key in `Key Bindings.json` like any other command
(see [`docs/KEYBINDINGS.md`](../KEYBINDINGS.md)):

```json
{ "keys": ["Ctrl+Alt+T"], "command": "select_theme" }
```

## Themes

Bundled: **Monokai** (default), **Dark**, **Light**, **Solarized Dark**,
**Solarized Light**, **Nord**, **Dracula**, **Gruvbox Dark**,
**High Contrast**, **WezTerm**, **Matrix**.

**Matrix** also ships slightly translucent (`"opacity": 0.92`) — see
[Set window opacity](window-opacity.md) to override that, or to fade any
other theme.

A theme may also name an icon set and an icon size (`"icons"` and
`"icon_size"`), so switching theme can change every icon in the panes — see
[Select icon set](select-icon-set.md) to override that, or to pick a set
without changing your colors.

It may name a **font** too (`"font"`), so switching theme can change the
typeface as well — eight of the eleven bundled themes do. See
[Select font](select-font.md) to override that, or to pick a family
without changing your colors.

Writing your own is one small JSON file of colors dropped into
`%APPDATA%/fman/Themes/` — see [`docs/THEMES.md`](../THEMES.md).

## Where it lives

- Command: `Plugins/Core/core/commands/theme.py` (`SelectTheme`)
- Colors, the font and the icon keys, theme discovery, live switching:
  `fman/impl/themes.py` and `fman/impl/theme_controller.py`
- Saved as `theme` in `%APPDATA%/fman/Local/Settings.json`
