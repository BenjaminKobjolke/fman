# Select font

Which font family fman draws its UI in. The default is the one fman has
always used on your platform; six more ship with it, and every font installed
on the machine is offered too.

This page is how to *use* the command. For the topic itself — which
families are bundled, what a theme may ask for, how to add your own and
how the bundled ones are vendored — see [`docs/FONTS.md`](../FONTS.md).

## Usage

1. Open [the command palette](../COMMAND_PALLETTE.md) with `Ctrl+Shift+P`.
2. Type *select font* and press `Enter`.
3. Pick a family. The list is every font Qt can see, with the active one
   preselected and marked `current`, and **Theme default** first.

It applies **immediately** — no restart — and is remembered across restarts.

**Theme default** is the way back: it forgets your choice so the active theme
decides again, which for a theme that names no font means fman's default for
the platform (`Roboto` on Windows, `Open Sans` on Linux, `Helvetica Neue` on
macOS).

There is a command for exactly that, so you do not have to scroll a list of
every font on the machine to find it: **Reset font**.

The list is long, because it is genuinely every installed family — type a few
letters of the one you want rather than scrolling. The palette matches on
initials too, so `jbm` finds *JetBrains Mono*.

### This is the family, not the size

`Alt+Up` and `Alt+Down` ([Pane font size](pane-font-size.md)) change how
**big** the file list's text is. This command changes **which typeface** the
whole UI uses. They are independent: zooming never changes the family, and
picking a font never resets a zoom.

### Fonts fman bundles

Six families ship with fman on top of the two it has always used (`Roboto`
and `Open Sans`), so a theme can ask for one without depending on what your
machine has installed:

| Family | The theme that uses it |
|--------|------------------------|
| JetBrains Mono | Dracula, WezTerm |
| Fira Code | Gruvbox Dark |
| IBM Plex Sans | Nord |
| Public Sans | Solarized Dark, Solarized Light |
| Share Tech Mono | Matrix |
| Atkinson Hyperlegible | High Contrast |

You can pick any of them under any theme — the pairing is only what that
theme asks for by default.

## Commands

| Command | In the palette | Default key binding |
|---------|----------------|---------------------|
| `select_font` | Select font | none |
| `reset_font` | Reset font | none |

Searching for *typeface*, *font family*, *change font*, *monospace*, *ui
font* or *text font* also finds **Select font**, and *default font*, *theme
font*, *reset typeface* or *clear font* find **Reset font**. Those are hidden
search terms: they match in the palette without ever being shown — see
[the command palette](../COMMAND_PALLETTE.md#hidden-search-keywords).

It can be bound like any other command in `Key Bindings.json`:

```json
{ "keys": ["Ctrl+Alt+F"], "command": "select_font" }
```

## Themes

A theme may name a font of its own, and switching theme applies it. Your own
choice **wins** and survives a theme switch, until you pick **Theme default**
or run **Reset font** — the same precedence
[Select icon set](select-icon-set.md) and
[Set window opacity](window-opacity.md) use:

1. Your **Select font** choice, if you have made one.
2. Otherwise the active theme's `"font"`.
3. Otherwise fman's default for the platform.

A family fman cannot find is **not** an error — Qt quietly falls back to its
own font. So if a pick appears to do nothing, the family is not installed
under that exact name.

Writing a theme that carries a font is one key in its JSON file; adding a
font of your own is a `.ttf` dropped into a plugin folder. Both are in
[`docs/FONTS.md`](../FONTS.md). Related:
[Select theme](select-theme.md), [Select icon set](select-icon-set.md),
[Pane font size](pane-font-size.md).

## Where it lives

- `src/main/resources/base/Plugins/Core/core/commands/theme.py` —
  `SelectFont`, `ResetFont` and `get_font_items`
- `src/main/resources/base/Plugins/Core/Command Keywords.json` — the hidden
  search terms
- `src/main/python/fman/impl/themes.py` — the `font` theme key, its
  validator, and `DEFAULT_FONT` per platform
- `src/main/python/fman/impl/theme_controller.py` — the theme-vs-user
  precedence, and the push on a switch
- `src/main/python/fman/impl/theme.py` — substitutes the family into the
  `$font_family` token in `Theme.css`
- `src/main/python/fman/impl/plugins/plugin.py` — registers every `.ttf` a
  plugin ships, searched recursively
- `src/main/resources/base/Plugins/Core/Fonts/` — the bundled families,
  vendored by `tools/fetch_google_fonts.bat`
- [`docs/FONTS.md`](../FONTS.md) — the topic itself
