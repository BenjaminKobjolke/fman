# Fonts

Which typeface fman draws its UI in: what ships with it, how to switch, what a
theme may ask for, and how to add your own.

This is the *family*, not the size. How big the file list's text is belongs to
[Pane font size](functions/pane-font-size.md) and `Theme.css`; the two are
independent, and neither undoes the other.

## Bundled families

fman ships eight families, so a theme can ask for a look without depending
on what the machine happens to have installed.

| Family | Kind | Used by | Licence |
|--------|------|---------|---------|
| **Roboto** | sans | the Windows default | Apache 2.0 |
| **Open Sans** | sans | the Linux default | Apache 2.0 |
| **JetBrains Mono** | monospace | Dracula, WezTerm | OFL 1.1 |
| **Fira Code** | monospace | Gruvbox Dark | OFL 1.1 |
| **IBM Plex Sans** | sans | Nord | OFL 1.1 |
| **Public Sans** | sans | Solarized Dark, Solarized Light | OFL 1.1 |
| **Share Tech Mono** | monospace | Matrix | OFL 1.1 |
| **Atkinson Hyperlegible** | sans | High Contrast | OFL 1.1 |

Roboto and Open Sans predate this feature — they are the families fman
has always drawn in. They ship as a **single face each** (Roboto's Bold,
Open Sans's Semibold), because that is the weight fman's UI asks for; the
other six ship Regular and Bold.

Those two are also the only families that are not on every platform: the
freeze step drops whichever is unused, since fman issue #480 was a font
failing to load on a system that never needed it.

| Build | Ships |
|-------|-------|
| Windows | Roboto + the six (Open Sans dropped) |
| Linux | Open Sans + the six (Roboto dropped) |
| macOS | the six only (both dropped; the default is the system's Helvetica Neue) |

See `build_impl/windows.py`, `mac.py` and `linux.py`. Each drops the whole
`Fonts/<Family>/` directory, so a licence never outlives the font it covers.

The six added for this feature were picked one per theme mood: a coding
monospace for the terminal palettes, a neutral sans for the low-contrast
ones, a CRT face for Matrix, and a typeface drawn for low vision for High
Contrast.

All eight live in `Plugins/Core/Fonts/<Family>/` with their licence beside
them — the OFL and the Apache License both require the copy to travel
with the font.

Monokai, Dark and Light name no font on purpose. Monokai *is* the pre-themes
look and is pinned by the tests; Dark and Light are the neutral pair.

Every family is offered under every theme — the pairing above is only what
each theme asks for by default.

## Switching

Open [the command palette](COMMAND_PALLETTE.md) (`Ctrl+Shift+P`) and run
**"Select font"**. The list is every family Qt can see — the bundled ones
*and* everything installed on your system — with the active one preselected
and marked `current`, and **Theme default** first.

Picking one applies it **immediately** — no restart — and remembers it across
restarts. **Theme default** forgets your choice so the active theme decides
again.

The palette has a **"Reset font"** command that does the same thing without
opening the picker — the way **Reset font size** undoes a zoom. Use it when
a theme you switched to keeps drawing in the family you once picked.

The list is long, because it really is every installed family: type a few
letters instead of scrolling. The palette matches initials too, so `jbm`
finds *JetBrains Mono*.

See [Select font](functions/select-font.md) for the command reference.

### A family fman cannot find is not an error

Qt quietly falls back to its own font. That is deliberate: fman cannot tell a
typo from a family you happen not to have installed, so it never refuses one.
If a pick appears to do nothing, the family is not installed under that exact
name.

## What a theme can ask for

A theme may name a font family beside its colors — one of the five things in
a theme file that are not colors, see [THEMES.md](THEMES.md):

```json
{
	"colors": { "pane_bg": "#000000" },
	"font": "Share Tech Mono"
}
```

The value is a family **name**, not a file: anything Qt can see, bundled or
installed (`Consolas`, `Menlo`, `DejaVu Sans Mono`). Leaving the key out means
"don't touch it", so switching theme always sets the family — back to fman's
default included.

Your own choice wins over the theme's and survives a theme switch, until you
pick **Theme default** again:

| # | Wins | Where it lives |
|---|------|----------------|
| 1 | Your **Select font** choice | `font` in `%APPDATA%/fman/Local/Settings.json` |
| 2 | The active theme's `"font"` | the theme's JSON file |
| 3 | fman's default for the platform | `DEFAULT_FONT` in `impl/themes.py` |

### The defaults

The default is what fman always used, now named rather than hardcoded in a
per-platform `Theme.css`:

| Platform | Default family |
|----------|----------------|
| Windows | `Roboto` |
| Linux | `Open Sans` |
| macOS | `Helvetica Neue` |

Two of those three are not quite what the old CSS said, and both changes
are deliberate:

- **Windows was `Roboto Bold`, which is not a family.** The bundled file is
  Roboto's Bold *face*; its name table says the family is `Roboto`, so that
  is what `QFontDatabase` registers. `font-family: "Roboto Bold"` therefore
  matched nothing and Qt had been quietly falling back for years. Naming
  the real family fixes that — and since the family holds only that one
  face, it still draws the bold weight fman always wanted.
- **macOS named no family at all** and drew in Qt's system font. It now
  follows the family fman already picks for its Mac context menus in
  `os_styles.qss`.

Linux is unchanged: `Open Sans.ttf` is a Semibold face, but its family
really is `Open Sans`, so that string always resolved.

## Adding your own font

Every `.ttf` in a plugin's directory is registered when that plugin loads, and
the search is **recursive**. So dropping a font into your own plugin folder —
or a subfolder of it — makes its family available to `Theme.css`, to a theme's
`font` key and to **Select font**, with no packaging step.

That is the same mechanism the bundled families use: they are simply the Core
plugin's.

To use it without writing a theme, set it in your own
`%APPDATA%/fman/Plugins/User/Settings/Theme.css`:

```css
* { font-family: "My Font"; }
```

That pins the family against every theme, the way pinning a color does.
**Select font** is the friendlier way to do the same thing, and unlike an edit
here it is undoable from the palette.

## Updating the bundled families

```
tools\fetch_google_fonts.bat
tools\fetch_google_fonts.bat --family "Fira Code"
```

The six OFL families come from [Google Fonts](https://fonts.google.com) via
its `download/list` endpoint, which hands back the static TTF URLs plus the
licence text. Committing the output is the point: fman must not need the
network to draw text. Add a family to `FAMILIES` in
`tools/fetch_google_fonts.py` first.

**Roboto and Open Sans are not in `FAMILIES`** and the script will not
touch them. They were vendored by hand long before it existed, and the
faces fman ships are not the ones a fresh fetch would return — re-fetching
would quietly restyle Windows and Linux. Their `LICENSE` files were written
once, by hand, from the Apache 2.0 text.

Two things the script is careful about, both learned the hard way:

- **Only static TTFs, Regular and Bold.** Qt 5 cannot read variable-font axes,
  so a variable file would give one weight and a synthesised bold — and it
  cannot load the woff2 that most font packages (`@fontsource` included) ship
  at all.
- **The directory name is read out of the font, not chosen.** It comes from
  the `name` table (typographic family, falling back to family), which is the
  string `QFontDatabase` reports and therefore the exact value a theme's
  `font` key has to carry. That is how Google's "Inter" was caught shipping
  only as the optical size `Inter 18pt` — which is why fman bundles Public
  Sans instead.

Share Tech Mono has no bold upstream; the script says so and Qt synthesises
one.

## Tests

`tools\run_theme_tests.bat` covers the fonts along with the themes
(`fman_unittest.impl.test_fonts`).

- **Every family ships a face** — at least one `.ttf`, not specifically a
  `Regular.ttf`: Roboto and Open Sans are single-face by design. A family
  directory with no font in it would be a name nothing can draw.
- **Every family ships a `LICENSE`**, and it is not empty. This is the guard
  that matters most: both the OFL and the Apache License require the copy to
  travel with the font, and a missing one is a distribution problem rather
  than anything a screenshot would reveal.
- **Every font file is really a TrueType.** `addApplicationFont` answers -1
  for anything else and the plugin loader only *reports* that, so a woff2
  that slipped in would be a font that silently never appears.
- A bundled theme's `font` must name a family fman actually **bundles**. Any
  installed family is legal in a theme you write, but a bundled theme naming
  one would look different on every machine.
- The **precedence** holds: the user's pick beats the theme's, the theme's
  beats the platform default, and clearing the override falls back through
  the same chain (`FontPrecedenceTest`).
- The user's saved font is validated like a theme's, so a hand-edited
  `Settings.json` cannot inject into the stylesheet that theme files are
  guarded from.
- The `$font_family` token must survive substitution into `Theme.css`, and
  is quoted — every bundled family except Roboto has a space in its name,
  which would otherwise fall apart inside the QSS declaration.

## Where it lives

- `src/main/python/fman/impl/themes.py` — the `font` theme key, its
  validator, `DEFAULT_FONT` per platform, and `build_tokens`
- `src/main/python/fman/impl/theme_controller.py` — the theme-vs-user
  precedence, and the push on a switch
- `src/main/python/fman/impl/theme.py` — substitutes the family into the
  `$font_family` token
- `src/main/resources/base/Plugins/Core/Theme.css` —
  `* { font-family: $font_family; }`, the one rule that applies it
- `src/main/python/fman/impl/plugins/plugin.py` — registers every `.ttf` a
  plugin ships, searched recursively
- `src/main/python/fman/impl/font_database.py` — the `QFontDatabase` wrapper
- `src/main/resources/base/Plugins/Core/core/commands/theme.py` — `SelectFont`
  (the picker) and `ResetFont` (the way back, `set_font(None)`)
- `src/main/resources/base/Plugins/Core/Command Keywords.json` — the hidden
  palette search terms for both
- `src/unittest/python/fman_unittest/impl/test_fonts.py` — the vendoring
  guards and the precedence tests
- `src/main/resources/base/Plugins/Core/Fonts/` — the bundled families,
  vendored by `tools/fetch_google_fonts.bat`
