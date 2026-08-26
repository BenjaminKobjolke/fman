# Select icon set

Which icons the file list draws, and how big. By default fman shows the ones
your operating system supplies; the bundled **Material** set gives a distinct
icon to each language, config file and well-known folder name instead.

This page is how to *use* the commands. For the topic itself — the sets, the
manifest format, vendoring — see [`docs/ICONS.md`](../ICONS.md).

## Usage

1. Open [the command palette](../COMMAND_PALLETTE.md) with `Ctrl+Shift+P`.
2. Type *select icon set* and press `Enter`.
3. Pick **Material** (or **System** to go back). The list shows every
   installed set, with the active one preselected and marked `current`.

It applies **immediately** — both panes redraw, no restart — and is
remembered across restarts.

**Set icon size** works the same way and offers 16, 20, 24, 32 and 48
pixels, plus **Theme default**. The rows grow with the icons, and the size
applies to the OS icons too, so it is useful even on **System**.

**Set icon color** recolors the set — Green, Cyan, Blue, Amber, Red,
Magenta, White or Grey, plus **Theme default**. Each icon keeps its own
shading, so it is a recolor rather than a silhouette. It has no effect on
**System**: those icons come from the OS, not from fman.

### The size follows the font zoom

`Alt+Up` and `Alt+Down` ([Pane font size](pane-font-size.md)) scale the icons
along with the text, in the same proportion, from whatever size is set here.
So at `48`, zooming in grows the icons from 48 — and *Set icon size* keeps
showing `48`, because the zoom is not saved as a size of its own. **Reset
font size** puts both back.

## Commands

| Command | In the palette | Default key binding |
|---------|----------------|---------------------|
| `select_icon_set` | Select icon set | none |
| `set_icon_size` | Set icon size | none |
| `set_icon_color` | Set icon color | none |
| `toggle_executable_icons` | Toggle real icons for programs and shortcuts | none |

The palette also finds **Select icon set** by *file icons*, *folder icons*,
*icon theme*, *icon set*, *material* and *vscode icons*; **Set icon size** by
*bigger icons*, *smaller icons*, *icon scale*, *large icons* and *row
height*; **Set icon color** by *icon tint*, *recolor icons*, *colorize
icons*, *colour icons* and *icon theme color*; and the toggle by *exe icon*,
*program icon*, *shortcut icon* and *application icon*.

Bind any of them to a key in `Key Bindings.json` like any other command (see
[`docs/KEYBINDINGS.md`](../KEYBINDINGS.md)):

```json
{ "keys": ["Ctrl+Alt+I"], "command": "select_icon_set" }
```

## Files that keep their OS icon

- **`.ico` files** always show themselves — an icon file *is* a picture of
  itself.
- **Programs and shortcuts** (`.exe`, `.lnk`) use the icon set by default.
  An icon set draws every program alike, while the OS icon says *which*
  program it is, so **Toggle real icons for programs and shortcuts** opts
  those two extensions back out. It is a toggle: run it again to undo.

## Themes

A theme may carry an icon set, a size and a color of its own (`"icons"`,
`"icon_size"` and `"icon_color"`), the same way **Matrix** carries an
opacity — and Matrix now carries all three, which is what makes its icons
green. Your own choice here **wins over the theme's** and survives a theme
switch, until you pick **Theme default** in *Set icon size* or *Set icon
color* — or **System** in *Select icon set* — to hand the decision back.

Writing your own set is a directory of SVGs plus a `manifest.json`, dropped
into `%APPDATA%/fman/Icons/` — [`docs/ICONS.md`](../ICONS.md) documents the
manifest format, the matching rules and how the bundled set is vendored.
Related: [Select theme](select-theme.md),
[Select font](select-font.md), [Set window opacity](window-opacity.md)
and [Pane font size](pane-font-size.md), which together with the icon
size decide how tall a row is.

## Where it lives

- `src/main/resources/base/Plugins/Core/core/commands/theme.py` —
  `SelectIconSet`, `SetIconSize`, `SetIconColor`
- `src/main/resources/base/Plugins/Core/core/commands/__init__.py` —
  `ToggleExecutableIcons`, and the pane font size commands that drive the
  icon zoom
- `src/main/python/fman/impl/model/icon_set.py` — the manifest and its
  lookup rules
- `src/main/python/fman/impl/model/icon_provider.py` — which icon a file
  actually gets
- `src/main/python/fman/impl/model/icon_tint.py` — the recolor
- `src/main/python/fman/impl/themes.py` — how the theme's and the user's
  choices are resolved against each other
- `src/main/resources/base/Icons/Material/` — the bundled set, vendored by
  `tools/fetch_material_icons.bat`
