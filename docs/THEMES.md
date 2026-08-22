# Themes

How fman colors and styles its UI, and how to customize it. This is
background for anyone touching theming, plus a quick "how do I change a
color" pointer.

## Two separate color sources — don't confuse them

fman's look comes from **two independent mechanisms**, not one:

1. **`QPalette`** — the actual colors (pane background, text, selection
   highlight, window chrome). Built in code, not configurable via a file:
   `src/main/python/fman/impl/application_context.py:316-343`
   (`ApplicationContext.palette`, a `cached_property`). Key entries:

   | `QPalette` role       | Color        | Meaning                    |
   |-----------------------|--------------|-----------------------------|
   | `QPalette.Base`       | `#131313`    | Pane / text-field background |
   | `QPalette.Text`       | white        | Pane / text-field foreground |
   | `QPalette.Window`     | `#2b2b2b`    | Window/dialog background     |
   | `QPalette.AlternateBase` | `#42403b` | Alternating row color       |
   | `QPalette.Highlight`  | Qt default   | Selection background         |

   Applied app-wide once: `result.setPalette(self.palette)` on the
   `QApplication` (`application_context.py:119`). A couple of variants exist
   for specific widgets — `main_window_palette` (line 362) tweaks `Window`,
   `progress_bar_palette` (line 367) tweaks inactive `Highlight`.

2. **`Theme.css`** — a QSS stylesheet, applied app-wide via
   `QApplication.setStyleSheet`. Handles font sizes, padding, borders, and
   the quicksearch popup's text colors — **not** pane background/foreground.
   Example rules from the base theme
   (`src/main/resources/base/Plugins/Core/Theme.css`):

   ```css
   * { font-size: 9pt; }
   .locationbar { padding: 0.25ex; border-bottom: 1px solid #262626; }
   .quicksearch-item-title { color: #c8c8c8; }
   ```

**Practical upshot:** if you want to change what a pane looks like
(background/text color), you're changing the `QPalette` in
`application_context.py` — there is currently no `Theme.css` hook for it.
`Theme.css` only reaches the handful of selectors below.

## Theme.css: files, selectors, and load order

Files, checked in order, each optional:

- `Plugins/Core/Theme.css` — base rules (all platforms).
- `Plugins/Core/Theme (Windows|Mac|Linux).css` — platform-specific
  additions/overrides.
- `%APPDATA%/fman/Plugins/User/Settings/Theme.css` (Windows; equivalent
  per-OS `Plugins/User/Settings/` folder elsewhere) — **the user override
  file**. This is the one you edit to customize a running install.

Any plugin can ship a `Theme.css`; loading happens per plugin at load time
(`src/main/python/fman/impl/plugins/plugin.py:130-159`), which locates the
base + platform variant (`self._config.locate('Theme.css', ...)`) and calls
`Theme.load(css_file)`.

`Theme` (`src/main/python/fman/impl/theme.py`) only understands a **fixed,
small set of CSS selectors** — it is not general QSS, it's a friendly
subset mapped to real Qt selectors (`_CSS_TO_QSS`, `theme.py:7-14`):

| CSS selector                    | Real Qt selector                    |
|----------------------------------|--------------------------------------|
| `*`                               | `*` (applies to everything)          |
| `th`                              | `QTableView QHeaderView::section`    |
| `.statusbar`                      | `QStatusBar, QStatusBar QLabel`      |
| `.locationbar`                    | `LocationBar:read-only`              |
| `.quicksearch-query`              | `Quicksearch QLineEdit`              |
| `.quicksearch-item`               | `Quicksearch QListView::item`        |

(`.quicksearch-item-title`, `-highlight`, `-hint`, `-description` are parsed
separately via a small CSS engine — `theme.py:62-97` — and read back by the
quicksearch popup's own paint code via `Theme.get_quicksearch_item_css()`,
rather than becoming QSS.)

Each `load()` call re-parses all loaded CSS files, converts every rule to
QSS text, concatenates it, and calls `QApplication.setStyleSheet(qss)`
(`theme.py:115-119`, `Theme._update_app`). So **the entire app stylesheet is
rebuilt and reapplied on every theme load** — any selector not in the table
above is silently dropped (`_get_qss_selectors`, `theme.py:107-114`, skips
unknown selectors via `KeyError`).

## The wildcard gotcha (why widgets sometimes look "stuck")

`* { font-size: 9pt; }` in the base `Theme.css` becomes a QSS `*` rule
applied to literally every widget. This has a side effect beyond font size:
**once any stylesheet touches a widget, Qt switches that widget from
palette-based rendering to the QSS style engine.** Two consequences seen in
this codebase:

- A widget that relies on `QPalette` colors alone may stop reflecting
  palette changes once the wildcard rule touches it, unless it also gets an
  explicit local QSS rule.
- QSS-rendered `QPlainTextEdit`/text widgets only draw the blinking text
  caret if `color`/`background-color` are set **explicitly** in that
  widget's own stylesheet — otherwise the caret silently stops rendering
  (hit by the text viewer, see
  [`docs/views/TEXT_VIEWER.md`](views/TEXT_VIEWER.md)).

**The fix pattern, used twice already:** apply a narrow, widget-local QSS
rule that targets only that widget's type selector — a local rule always
wins over the app-wide `*` rule.

- [Pane font size](functions/pane-font-size.md) — zoom sets
  `FileListView { font-size: Npt; }` locally on each pane's file view,
  beating the global `*` rule regardless of active theme.
- [Text viewer](views/TEXT_VIEWER.md) — sets
  `QPlainTextEdit { color: ...; background-color: ...; }` locally, with the
  colors read live from `QPalette` (see next section) rather than
  hardcoded, so it stays theme-correct.

## Writing a new widget that should follow the theme

- **For colors:** read the inherited `QPalette` rather than hardcoding —
  `widget.palette().color(QPalette.Base)` for background,
  `QPalette.Text`/`QPalette.WindowText` for foreground,
  `QPalette.Highlight` for selection. In a delegate/paint routine, use
  `option.palette` (see `src/main/python/fman/impl/view/__init__.py:354`,
  `pen = QPen(option.palette.light().color())`). This is exactly what the
  text viewer does — it copies its colors from the file view's live palette
  (`widget._file_view.palette()`) instead of hardcoding `#131313`.
- **For sizes/padding shared with the rest of the UI:** either add a
  selector to `_CSS_TO_QSS` (touches core, affects every theme file) or read
  the live effective value off an existing styled widget, the way
  pane-font-size reads `QFontInfo(view.font()).pointSize()` rather than a
  constant.
- **If you must set a local stylesheet** (e.g. to force a color the QSS
  engine would otherwise swallow, per the caret gotcha above): keep it a
  narrow type-selector rule, not `*`, and source the color values from
  `QPalette`/a live widget so a custom theme still gets reflected.

## How to change fman's colors right now

- **Font sizes, paddings, quicksearch text colors:** edit your user
  `Theme.css` (`%APPDATA%/fman/Plugins/User/Settings/Theme.css` on
  Windows) using the selectors in the table above.
- **Pane background/foreground/selection colors:** not exposed via
  `Theme.css` today — they're the fixed `QPalette` in
  `application_context.py:316-343`. Changing them means editing that file
  (and rebuilding), or adding a widget-local QSS override on the specific
  widget you want to look different (see the fix pattern above).
