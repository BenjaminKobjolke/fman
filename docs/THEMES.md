# Themes

How fman colors and styles its UI, how to switch themes, and how to write
your own.

## Switching theme

Open the [command palette](COMMAND_PALLETTE.md) (`Ctrl+Shift+P`) and run
**"Select theme"**. The list shows every installed theme, with the active one
preselected and marked `current`. Picking one applies it **immediately** — no
restart — and remembers it across restarts.

Bundled themes: **Monokai** (the default, fman's classic look), **Dark**,
**Light**, **Solarized Dark**, **Solarized Light**, **Nord**, **Dracula**,
**Gruvbox Dark**, **High Contrast**, **WezTerm**, **Matrix**.

What they look like, two seconds each (regenerate with
`tools\demo_themes_record.bat` — see [DEMOS.md](DEMOS.md)):

![themes](../media/demos/themes/themes.gif)

Two things do *not* recolor live:

- A **file viewer that is already open** (text, image or video). Those read
  their colors from the pane when they open, so close and reopen the file.
- **Context menus** on Windows and macOS. They deliberately imitate the
  native OS menu, and stay light under every theme — see
  [Not themed](#not-themed).

## Colors are data: one token map

Every color fman draws comes from one flat map of named **color tokens**
(`src/main/python/fman/impl/themes.py`, `DEFAULT_COLORS`). Those tokens feed
three consumers, which is why a theme cannot style one part of the UI and
leave another behind:

| Consumer | What it colors | How the tokens get there |
|----------|----------------|--------------------------|
| `src/main/resources/base/styles.qss` | File list, header, selection, inputs, status bar, overlays, quicksearch popup | `$token` placeholders, substituted by `Theme` (`impl/theme.py`) |
| `Plugins/Core/Theme.css` | Quicksearch **item** text: title, highlight, hint, description, item dividers, location-bar divider | same substitution — `Theme.load` substitutes every CSS file it loads |
| `QPalette` | Roles Qt draws itself: window chrome, tooltips, buttons, the pane focus rectangle, the "Loading…" text; also what the text viewer samples | `build_palette` & co. in `impl/themes.py` |

`ApplicationContext` reads the saved theme name before any plugin loads
(`%APPDATA%/fman/Local/Settings.json`, key `theme`) because the `QPalette`
has to exist when the `QApplication` is created.

## Writing a theme

A theme is **one JSON file** listing only the colors it changes (plus,
optionally, an [opacity](#opacity)):

```json
{
	"colors": {
		"pane_bg": "#2e3440",
		"pane_fg": "#d8dee9",
		"pane_selected_fg": "#88c0d0"
	}
}
```

- **File name is the theme name.** `Nord.json` shows up as *Nord*.
- Put it in `%APPDATA%/fman/Themes/` (Windows; `~/Library/Application
  Support/fman/Themes` on macOS, `~/.config/fman/Themes` on Linux). A file
  there shadows a bundled theme of the same name.
- Bundled themes live in `src/main/resources/base/Themes/`.
- `Monokai.json` is `{}` — the defaults *are* Monokai, so there is no second
  copy of them to drift.
- Unknown token names and invalid color values are ignored, not fatal: a
  typo costs you that one color, it never stops fman from starting.
- Values are any color Qt understands (`#rgb`, `#rrggbb`, `white`). A value
  containing `;`, `{` or `}` is rejected — it would break out of the
  stylesheet rule it lands in.

### You only need the 15 core tokens

Tokens that are not listed **inherit from a parent token** before falling
back to the default. So setting `pane_bg` alone also moves `base_bg` (what
the text viewer paints on), and setting `border` alone moves every separator
and bevel in the quicksearch popup.

**Core tokens** — no parent, set these:

| Token | What it colors |
|-------|----------------|
| `pane_bg` | File list / dialog / overlay / filter-bar background |
| `pane_fg` | File rows |
| `pane_fg_dir` | Directory rows (defaults to `bright_fg`) |
| `pane_selected_fg` | Text of selected files |
| `pane_cursor_bg` | Cursor row, and the pane's focus rectangle |
| `header_bg` | Column-header gradient, input borders |
| `muted_fg` | Header text, labels, checkboxes, item descriptions |
| `bright_fg` | Input text, status-bar text, highlighted matches |
| `border` | Overlay / filter-bar border, status-bar top edge |
| `input_bg` | Text fields (rename editor, prompts) |
| `window_bg` | Window and dialog chrome |
| `statusbar_bg_top` | Status-bar gradient |
| `popup_bg` | Quicksearch / command-palette background |
| `popup_item_fg` | Command-palette entry titles |
| `popup_selected_bg` | Selected entry in the palette |

Separators inherit `border`, never the surface they sit on: a divider that
defaults to `popup_bg` is invisible by construction, which is what made the
command palette read as one solid block in early versions of the light theme.

**Derived tokens** — override only if the inherited value looks wrong:

| Token | Inherits from |
|-------|---------------|
| `base_bg` | `pane_bg` |
| `readonly_fg` | `muted_fg` |
| `input_border`, `locationbar_border`, `palette_midlight` | `header_bg` |
| `statusbar_bg_bottom` | `statusbar_bg_top` |
| `popup_query_border`, `popup_query_inner_border`, `popup_divider_top`, `popup_divider_bottom`, `popup_input_border` | `border` |
| `popup_input_bg` | `input_bg` |
| `popup_input_fg` | `bright_fg` |
| `popup_input_border_top` / `_left` / `_right` | `popup_input_border` |
| `main_window_bg`, `button_bg` | `window_bg` |
| `alt_row_bg` | `pane_cursor_bg` |
| `button_fg` | `muted_fg` |
| `palette_mid`, `palette_dark`, `palette_shadow` | `button_bg` |

### Opacity

A theme may also make fman's window see-through. This is the one thing in a
theme file that is *not* a color, so it sits beside `colors`, not in it:

```json
{
	"colors": { "pane_bg": "#000000" },
	"opacity": 0.92
}
```

- `1.0` is fully opaque, `0.3` the most transparent fman allows. A value
  outside that range, or one that is not a number, is ignored like any other
  typo — the theme just doesn't change the opacity.
- The whole window fades, text included. fman does not do background-only
  translucency. Dialogs are separate windows and stay opaque.
- Leaving the key out means "don't touch it", which resolves to fully
  opaque — not "inherit from the previous theme". Switching themes therefore
  always sets the opacity, back to 1.0 included.
- The user's own setting wins over the theme's: see
  [Set window opacity](functions/window-opacity.md). Their choice survives a
  theme switch until they pick **Theme default** again.
- Bundled example: `Matrix.json`.

### Not themed

- **`QMenu` in `os_styles.qss`** (Windows/macOS context menus) — these copy
  the native OS menu on purpose, which is why they are light while fman is
  dark. Theming them is a separate decision; the values stay literal.
- **`QPalette.Highlight`** — never set, so Qt's Fusion style supplies it.
  This is what the progress bar uses.
- **Sizes, padding and fonts** — themes are colors (and
  [opacity](#opacity)) only. For those, see `Theme.css` below.

## Theme.css: fonts, padding, and user overrides

Separate from the color tokens, fman merges a small friendly stylesheet from
these files, each optional, in order:

- `Plugins/Core/Theme.css` — base rules (all platforms).
- `Plugins/Core/Theme (Windows|Mac|Linux).css` — platform-specific.
- `%APPDATA%/fman/Plugins/User/Settings/Theme.css` — **the user override
  file.** It loads last, so it wins over every theme. Edit this to change
  font sizes or padding, or to pin a color a theme keeps changing.

Put *only what you change* in that file. Copying the whole base `Theme.css`
into it copies its color literals too, and those then override every theme —
the classic symptom is a command palette that stays light-on-dark after
switching to a light theme.

Any plugin can ship a `Theme.css`; it is loaded per plugin at load time
(`impl/plugins/plugin.py`). `Theme` (`impl/theme.py`) understands only a
fixed set of selectors, mapped to real Qt ones (`_CSS_TO_QSS`):

| CSS selector | Real Qt selector |
|--------------|------------------|
| `*` | `*` (everything) |
| `th` | `QTableView QHeaderView::section` |
| `.statusbar` | `QStatusBar, QStatusBar QLabel` |
| `.locationbar` | `LocationBar:read-only` |
| `.quicksearch-query` | `Quicksearch QLineEdit` |
| `.quicksearch-item` | `Quicksearch QListView::item` |

(`.quicksearch-item-title`, `-highlight`, `-hint` and `-description` are
parsed separately by a small CSS engine and read back by the popup's own
paint code via `Theme.get_quicksearch_item_css()`, rather than becoming QSS.)

Your `Theme.css` may contain `$` freely — substitution leaves unknown names
alone. To use a theme's color in it, write the token: `color: $pane_fg;`.

## The wildcard gotcha (why widgets sometimes look "stuck")

`* { font-size: 9pt; }` in the base `Theme.css` becomes a QSS `*` rule
applied to every widget. This has a side effect beyond font size: **once any
stylesheet touches a widget, Qt switches that widget from palette-based
rendering to the QSS style engine.** Two consequences seen in this codebase:

- A widget relying on `QPalette` colors alone may stop reflecting palette
  changes once the wildcard rule touches it, unless it also gets an explicit
  local QSS rule.
- QSS-rendered `QPlainTextEdit`/text widgets only draw the blinking caret if
  `color`/`background-color` are set **explicitly** in that widget's own
  stylesheet (hit by the text viewer, see
  [`docs/views/TEXT_VIEWER.md`](views/TEXT_VIEWER.md)).

**The fix pattern:** apply a narrow, widget-local QSS rule targeting only
that widget's type selector — a local rule always wins over the app-wide `*`
rule, and over the theme.

- [Pane font size](functions/pane-font-size.md) — sets
  `FileListView { font-size: Npt; }` locally, so it survives a theme switch.
- [Text viewer](views/TEXT_VIEWER.md) — sets `QPlainTextEdit { color: …;
  background-color: …; }` locally, with the colors read live from the pane's
  `QPalette` rather than hardcoded.

## Writing a new widget that should follow the theme

- **Colors:** read the inherited `QPalette` rather than hardcoding —
  `widget.palette().color(QPalette.Base)` for background,
  `QPalette.Text`/`QPalette.WindowText` for foreground, `QPalette.Highlight`
  for selection. In a delegate/paint routine use `option.palette`
  (`impl/view/__init__.py`). Never read `fman.impl.themes` directly from a
  plugin: the palette is the supported way to get theme colors.
- **Sizes/padding shared with the rest of the UI:** either add a selector to
  `_CSS_TO_QSS` (touches core, affects every theme file) or read the live
  effective value off an existing styled widget, the way pane-font-size reads
  `QFontInfo(view.font()).pointSize()`.
- **If you must set a local stylesheet:** keep it a narrow type-selector
  rule, not `*`, and source the colors from `QPalette`/a live widget so a
  theme switch still reaches it.

## Tests

`tools/run_theme_tests.bat` runs the engine's theme tests. Two of them are
guards worth knowing about:

- Neither `styles.qss` nor `Theme.css` may contain a color literal, and
  every `$token` in them must exist — a mistyped placeholder would survive
  substitution and make the CSS parser reject the file, taking the whole
  Core plugin down.
- `build_palette(DEFAULT_COLORS)` is asserted against the exact `QPalette`
  fman used before themes existed, so the default look cannot drift.
- Every bundled theme is checked for **legibility**, not just validity: text
  pairs (entry title, matched characters, shortcut hint, description, file
  and directory rows, column headers) must clear a 4.5:1 WCAG contrast
  ratio, separators must be visible against the popup, and the selected row
  must stand out from it. Monokai is exempt — it *is* the pre-themes look,
  pinned by the tests above, so it cannot be recolored to satisfy a ratio.
  A bundled theme's optional `opacity` is validated the same way, and the
  count of bundled themes is asserted, so adding a file is a deliberate act.
  A new theme has to pass; add it to `src/main/resources/base/Themes/` and
  run the bat.
