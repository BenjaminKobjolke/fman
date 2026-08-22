# Text viewer

An in-pane viewer that shows a file's contents directly inside the active
pane, replacing the file list until closed. It exists so you can peek at (or
make a quick edit to) a text file without leaving fman or waiting on an
external editor to launch. Opens read-only; a viewer-scoped command palette
can switch eligible files to editable — see [Editing](#editing) below.

## Usage

1. Put the cursor on a file and run **"View file"** from the command palette.
2. The file's contents fill the active pane, in place of the file list.
3. Navigate with the mouse or keyboard: arrow keys move the cursor,
   **Shift+arrow** selects text, the mouse selects too, and long lines wrap
   to the pane width.
4. Press **Escape**, **Enter**, or **Backspace** to close the viewer and
   return to the file list, with the cursor back on the same file.
5. Press **Tab** to switch to the other pane — same as the normal file list.
   The viewer stays open in this pane; pressing **Tab** again brings focus
   straight back to it. (Tab only switches panes in view mode — see
   [Editing](#editing).)
6. Press **Ctrl+Shift+P** to open the viewer's own command palette (see
   below) instead of closing with Escape/Enter/Backspace.

There's no default key binding for opening the viewer — see
[`docs/functions/view-file.md`](../functions/view-file.md) for the command
itself.

## Editing

The viewer opens read-only. Press **Ctrl+Shift+P** to open its own command
palette — a fuzzy-search picker scoped to this viewer, separate from fman's
global command palette (which can't reach the viewer anyway, since it only
searches the file-list widget and that's hidden while viewing).

**View-mode entries:** *Exit viewer*, *Edit file*, *Reload from disk*,
*Increase font size*, *Decrease font size*, *Reset font size*.

**Edit-mode entries:** *Save file*, *Save file as…*,
*Revert / reload from disk*, *Increase font size*, *Decrease font size*,
*Reset font size*, *Exit viewer*.

Notes:

- **Not every file can be edited.** *Edit file* only makes the buffer
  editable if the file wasn't [size-truncated](#behaviour) and its bytes are
  strict UTF-8 — the same replacement decoding used for display is lossy, so
  saving it back would corrupt the original file. If a file doesn't qualify,
  *Edit file* shows an alert explaining why instead of entering edit mode.
- **Tab behaves differently in edit mode.** In view mode Tab switches panes
  (see above). Once editing, Tab types a literal tab character instead —
  pane-switching would otherwise be a constant risk of the wrong keystroke
  discarding your place. Use the palette's *Exit viewer* to leave edit mode.
- **Unsaved changes are protected.** *Exit viewer* prompts
  Save / Discard / Cancel if the buffer has unsaved edits;
  *Revert / reload from disk* prompts Discard / Cancel. The same protection
  applies if you run **View file** again on a *different* file while this
  pane's viewer has unsaved edits — the new file isn't opened until you
  save, discard, or cancel.
- **Line endings.** `QPlainTextEdit` normalizes all line endings to `\n`
  internally, so saving a file that used CRLF rewrites it with LF. A known,
  accepted limitation — re-open the file in an external editor first if you
  need CRLF preserved.
- **Save file as…** prompts for a full destination path and writes there;
  the viewer then continues editing/saving that new path.

## Zoom

The viewer has its own font-size zoom, independent of the file-list panes'
zoom ([pane font size](../functions/pane-font-size.md)):

1. Whatever key(s) you have **Increase font size** / **Decrease font size**
   bound to (`Alt+Up` / `Alt+Down` by default, from `Key Bindings.json`) also
   zoom the viewer's text — no separate binding to learn. This works in the
   viewer whether or not it's in edit mode, and doesn't interfere with typing.
2. The same **Increase font size** / **Decrease font size** actions are also
   in the viewer's own command palette (Ctrl+Shift+P), each showing its
   current shortcut as a hint, plus a palette-only **Reset font size**.
3. The chosen size is remembered separately from the pane list's own zoom —
   survives closing/reopening the viewer and restarting fman — until reset.

Rebinding `increase_pane_font_size`/`decrease_pane_font_size` in
`Key Bindings.json` changes what the viewer listens for too, since it looks
up the *current* binding rather than hardcoding `Alt+Up`/`Alt+Down`.

## Behaviour

- **Read-only by default.** Content can always be navigated and selected
  (e.g. to copy); becomes writable only after *Edit file* — see
  [Editing](#editing).
- **Word-wrapped.** Lines wrap at the pane's width rather than requiring
  horizontal scrolling.
- **Size-capped.** At most 2 MB of a file is read; larger files are
  truncated with a trailing notice, so opening a huge or binary-ish file
  can't freeze the UI.
- **Encoding-safe.** Content is decoded as UTF-8 with invalid bytes replaced
  (`�`) rather than guessing an encoding or raising on non-UTF-8 files.
- **Per-pane, one at a time.** Viewing a new file while one is already open
  in that pane replaces it; the other pane is unaffected.
- **Plain text only.** `.md` is shown as raw text, not rendered.
- **Follows the active theme.** Background/foreground match the file list's
  actual palette colors, not a hardcoded value — see
  [`docs/THEMES.md`](../THEMES.md).

## Why it works while the file list is hidden

fman's keyboard shortcuts are not global — they only fire for the file list
widget specifically (`FileListView.key_press_event_filter` →
`Controller.handle_shortcut`). The viewer is a separate Qt widget
(`QPlainTextEdit`) added to the same pane's layout, with the file list
hidden underneath it. Once it has keyboard focus, arrow keys reach it
directly instead of moving the (hidden) file cursor.

The same applies to **Tab**: it's normally bound to `switch_panes`
(`Key Bindings.json`) and only reaches that binding because
`FileListView.key_press_event_filter` forwards it — a hidden file list can't
receive key events at all. The viewer's `keyPressEvent` explicitly
intercepts `Tab`/`Shift+Tab` and calls `switch_panes` itself
(`pane.run_command('switch_panes')`) so the pane's own Tab binding still
works while the file list underneath is hidden. `show_text_viewer` also
re-points the pane widget's Qt focus proxy at the viewer
(`widget.setFocusProxy(view)`, normally the file list, see
`DirectoryPaneWidget.__init__`), so `switch_panes` tabbing back into this
pane focuses the viewer again instead of the hidden file list.

## Two Qt quirks this had to work around

Both were only found by testing real keyboard interaction, not by reading
Qt's docs — worth knowing if this code needs touching again:

- **`setReadOnly(True)` disables *all* keyboard cursor movement, not just
  editing.** In this Qt build, a read-only `QPlainTextEdit` silently ignores
  Right/Left/Shift+Right/etc. — the cursor never moves and nothing gets
  selected, even though the widget reports having focus. Fixed by calling
  `setTextInteractionFlags(Qt.TextSelectableByKeyboard |
  Qt.TextSelectableByMouse)` right after `setReadOnly(True)`, which restores
  keyboard navigation and selection while keeping the widget non-editable.
- **The app-wide theme silently hides the blinking caret.** `Theme.css`'s
  `* { font-size: ...pt; }` wildcard rule (applied via
  `QApplication.setStyleSheet`) touches every widget, including this one.
  Once *any* stylesheet touches a widget, Qt switches it from
  palette-based rendering to the QSS style engine — which only draws the
  blinking caret if `color`/`background-color` are set explicitly in that
  widget's own stylesheet. This is the same wildcard-rule problem
  [pane font size](../functions/pane-font-size.md) already works around for
  the file list (`FileListView { font-size: ...pt; }` beats the app-wide
  `*` rule). Fixed the same way: the viewer sets its own
  `QPlainTextEdit { color: ...; background-color: ...; }` — but with colors
  read live from the file view's own `QPalette` (`Base`/`Text`) rather than
  a hardcoded value, so the caret renders *and* matches whatever theme is
  active, including a custom `Theme.css`/palette. See
  [`docs/THEMES.md`](../THEMES.md) for how fman themes actually work.

## Implementation

The feature is split across a few small modules, partly to stay under the
project's 300-line-per-file cap and partly because the split lines up with
genuinely separate concerns (reading a file vs. the Qt widget vs. zoom):

- `src/main/resources/base/Plugins/Core/core/textviewer_io.py` — pure (no Qt)
  file-reading helpers, factored out so they're usable/testable independent
  of the widget:
  - `read_capped(path)` → `(data, truncated)`, the capped byte read.
  - `decode_for_display(data, truncated)` — UTF-8-with-replace decode plus
    the truncation notice.
  - `is_editable(data, truncated)` — `False` if the read was truncated or the
    bytes aren't strict UTF-8, else `True`. Drives whether *Edit file* is
    allowed (see [Editing](#editing)).
  - `load_for_view(path)` → `(display_text, editable)` — the full pipeline
    (the three above, chained), used by both the initial open
    (`show_text_viewer`) and *Revert* so neither repeats the sequence.
  - `read_text_for_view(path)` — `load_for_view` minus the editability half;
    a plain "read this file for display" helper.
- `src/main/resources/base/Plugins/Core/core/settings.py` —
  `get_setting(json_name, key)` / `save_setting(json_name, key, value)`, the
  generic "one key in a JSON settings file, `None` clears it" pattern.
  Extracted after it turned out to be duplicated verbatim (just a different
  key) between the pane font-size feature's own settings functions
  (`core/commands/__init__.py`) and this feature's
  (`core/textviewer_zoom.py`, below).
- `src/main/resources/base/Plugins/Core/core/font_size.py` — `clamp_font_size`
  and the min/max bounds, shared verbatim by both this feature and
  [pane font size](../functions/pane-font-size.md) so the two zoom features
  step/clamp identically. Split into its own module (rather than one
  importing the other) because `core/commands/__init__.py` imports
  `core/textviewer.py` at load time — the reverse import would be circular.
- `src/main/resources/base/Plugins/Core/core/key_bindings.py` —
  `get_shortcuts_for_command(key_bindings, command)` (which shortcut(s) the
  user currently has a command bound to, in the merged
  `Key Bindings.json`) and `format_shortcut_hint(shortcuts)` (join +
  Mac-symbol substitution for display). Also shared with — and, after this
  feature, factored out of — `core/commands/__init__.py`'s `CommandPalette`,
  which uses the same two functions for its own hint display. Same
  circular-import reason as `font_size.py`.
- `src/main/resources/base/Plugins/Core/core/textviewer_zoom.py` — the
  viewer's own zoom, independent of pane font size (own settings key
  `text_viewer_font_size` in `Core Settings.json` via `core/settings.py`, own
  base-size fallback): `get_saved_view_font_size`, `save_view_font_size`,
  `effective_view_font_size` (reads the live widget's `QFontInfo` as the
  step-from base when nothing's saved yet — same technique
  `core/commands/__init__.py`'s `_effective_font_size` uses for the file
  list), `change_view_font_size`, `reset_view_font_size` (these two take an
  `apply_size(size_or_None)` callback rather than touching a stylesheet
  directly, keeping this module PyQt-styling-agnostic), and
  `zoom_delta_for(key_event, key_bindings)` — the pure keystroke-matching
  function: builds a `QtKeyEvent` (`fman.impl.util.qt.key_event`, the same
  class `Controller.handle_shortcut` uses) from the raw Qt event and checks
  it against `get_shortcuts_for_command`'s result for
  `increase_pane_font_size`/`decrease_pane_font_size`, so it always follows
  the user's actual configured shortcut rather than a hardcoded
  `Alt+Up`/`Alt+Down`.
- `src/main/resources/base/Plugins/Core/core/textviewer.py`:
  - `_caret_fix_css(bg, fg, font_size=None)` — pure helper building the
    caret-fix stylesheet rule from the given colors, with the zoom override
    folded into the same local rule when given.
  - `_confirm_close(view)` — shared save/discard/cancel prompt for a
    mid-edit, unsaved view. Returns whether it's safe to close/replace it.
    Used by `PaneTextView._exit_with_dirty_check` *and* by
    `show_text_viewer` before it replaces the pane's currently open view, so
    running **View file** again on a different file can't silently discard
    unsaved edits in the one already open.
  - `PaneTextView(QPlainTextEdit)` — the viewer/editor widget. Tracks
    `_editable` (can this file be edited at all) and `_editing` (is it
    currently in edit mode) separately. `keyPressEvent`:
    - `Ctrl+Shift+P` always opens the viewer-scoped palette
      (`_open_palette`/`_suggest_actions`/`_get_actions`, built on the same
      `show_quicksearch`/`QuicksearchItem` API as fman's global command
      palette, filtered with `core.quicksearch_matchers.contains_chars`).
    - A zoom-shortcut match (via `zoom_delta_for`) is checked next, before
      the edit-mode passthrough, so it zooms rather than getting typed into
      the buffer.
    - While `_editing`, everything else (including Tab) is forwarded to
      `QPlainTextEdit`'s native handling — Exit/Save/Revert become
      palette-only so a stray keystroke can't lose focus or discard edits.
    - Otherwise (view mode), Escape/Enter/Return/Backspace close and
      Tab/Shift+Tab switch panes, as before.
    - Action methods: `_enter_edit_mode`, `_write` (shared by `_save`/
      `_save_as`), `_save`, `_save_as`, `_revert`, `_exit_with_dirty_check`,
      `_apply_font_size` (the `apply_size` callback passed to
      `change_view_font_size`/`reset_view_font_size`). Dirty-checking reads
      `self.document().isModified()`, which `setPlainText`/
      `setModified(False)` reset naturally.
  - `show_text_viewer(pane, url)` / `close_text_viewer(pane_widget)` — swap
    the viewer in/out of the pane's own `QVBoxLayout`
    (`pane._widget.layout()`), toggling `pane._widget._file_view`'s
    visibility and the pane widget's focus proxy. Both are
    `@run_in_main_thread`, since fman commands run on a background thread.
    Focus is grabbed via a deferred `QTimer.singleShot(0, view.setFocus)`
    rather than immediately, since the command palette's modal dialog
    restores focus to the (now hidden) file view as it closes, right before
    this code runs — grabbing focus synchronously would get clobbered by
    that restore.
- `src/main/resources/base/Plugins/Core/core/commands/__init__.py` —
  `ViewFile` (`DirectoryPaneCommand`), the palette command that triggers this;
  see [`docs/functions/view-file.md`](../functions/view-file.md). Also where
  `increase_pane_font_size`/`decrease_pane_font_size`/`reset_pane_font_size`
  live (pane font-size zoom, reused by `core/textviewer_zoom.py` as above).
- Tests, split the same way as the production modules:
  - `core/tests/test_textviewer_io.py` — `read_text_for_view`/`read_capped`'s
    byte cap and truncation notice, `is_editable`'s truncation/encoding
    rules, and `load_for_view`'s combined text+editability result.
  - `core/tests/test_textviewer_zoom.py` — `zoom_delta_for`'s shortcut
    matching, including that it follows a rebind rather than only the
    default `Alt+Up`/`Alt+Down`.
  - `core/tests/test_textviewer.py` — `_caret_fix_css`'s color/font-size
    substitution and selector.
  - The remaining Qt-specific behaviour (interaction flags, actual caret
    paint, Tab/focus-proxy switching, the palette dialog itself,
    save/revert/exit prompts, the actual zoom application) was verified
    interactively and with a headless `QTest.keyClick` script rather than an
    automated test, since it depends on real focus/paint/modal behaviour
    that unit tests don't exercise well.
