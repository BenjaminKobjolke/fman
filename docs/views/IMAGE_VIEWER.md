# Image viewer

An in-pane viewer that shows an image directly inside the active pane,
replacing the file list until closed — the [text viewer](TEXT_VIEWER.md)'s
counterpart for image files. It exists so you can peek at a `.png`/`.jpg`/
`.gif`/etc. without leaving fman or waiting on an external image app to
launch. Always read-only.

## Usage

1. Put the cursor on an image file and run **"View file"** from the command
   palette — the same command as the text viewer; see
   [`docs/functions/view-file.md`](../functions/view-file.md) for how it
   picks which viewer to open.
2. The image fills the active pane, in place of the file list, scaled to fit
   the pane by default.
3. Press **Escape**, **Enter**, or **Backspace** to close the viewer and
   return to the file list, with the cursor back on the same file.
4. Press **Tab** to switch to the other pane — same as the normal file list.
   The viewer stays open in this pane; pressing **Tab** again brings focus
   straight back to it.
5. Press **Ctrl+Shift+P** to open the viewer's own command palette (see
   below) instead of closing with Escape/Enter/Backspace.

## Zoom

The viewer has its own scale zoom, independent of the
[text viewer's font-size zoom](TEXT_VIEWER.md#zoom) and the file-list panes'
zoom ([pane font size](../functions/pane-font-size.md)):

1. Whatever key(s) you have **Increase font size** / **Decrease font size**
   bound to (`Alt+Up` / `Alt+Down` by default, from `Key Bindings.json`) also
   zoom the image — the same shortcut the text viewer reuses, so there's no
   separate binding to learn.
2. The viewer's own command palette (Ctrl+Shift+P) has **Zoom in** /
   **Zoom out** (showing the same shortcut as a hint), plus **Fit to
   window**, **Actual size (100%)**, and **Reset zoom** (Fit to window and
   Reset zoom both return to fit mode).
3. The chosen scale is remembered — survives closing/reopening the viewer
   and restarting fman — until reset (or Fit to window) clears it back to
   fit mode.
4. Zooming in from fit mode steps from whatever scale is *currently on
   screen*, not a hardcoded value — so the image doesn't jump when you first
   zoom in.

## Pan

Once zoomed in past the pane's size, scrollbars appear and the **arrow
keys** pan the image (they fall through to the underlying scroll area,
same as any scrollable widget). In fit mode there's nothing to pan — the
whole image is always visible.

## Behaviour

- **Read-only.** There's no edit mode — unlike the text viewer, an image
  can't be modified in place.
- **Animated GIFs play.** A `.gif` animates automatically while open;
  scaling (fit or explicit) applies to the animation, not just a static
  frame.
- **Per-pane, one at a time.** Opening an image while a text viewer (or
  another image) is open in that pane replaces it, and vice versa — both
  share the same pane mount slot; the other pane is unaffected.
- **Follows the active theme.** The letterbox background matches the file
  list's actual palette color, not a hardcoded value — see
  [`docs/THEMES.md`](../THEMES.md).
- **Recognized extensions:** `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`,
  `.webp`, `.ico`, `.svg`. Anything else opens in the
  [text viewer](TEXT_VIEWER.md) instead.

## Bindable commands

Beyond zoom (already bindable via the pane font-size shortcut, above, and
still read from `Key Bindings (<OS>).json`), the viewer's other actions are
viewer-only pseudo-commands you can bind your own key to in your own
`Viewer Key Bindings (<OS>).json` — a **separate file**, see
[`docs/KEYBINDINGS.md`](../KEYBINDINGS.md#viewer-specific-bindings). A
rebind always wins over the default key listed below.

| Command                | Default key            | Action                |
|-------------------------|------------------------|------------------------|
| `image_reset_zoom`      | *(none — palette only)* | Fit to window         |
| `image_actual_size`     | *(none — palette only)* | Actual size (100%)    |
| `viewer_close`          | Escape/Enter/Backspace | Close viewer           |
| `viewer_switch_panes`   | Tab                    | Switch panes           |
| `viewer_open_palette`   | Ctrl+Shift+P           | Open viewer command palette |

## Why it works while the file list is hidden

Same mechanism as the text viewer — see
[`docs/views/TEXT_VIEWER.md`#why-it-works-while-the-file-list-is-hidden](TEXT_VIEWER.md#why-it-works-while-the-file-list-is-hidden).
The image viewer reuses the identical pane-mounting glue
(`core/textviewer_pane.py`), so the same explanation applies verbatim: a
Qt widget replaces the (hidden) file list in the pane's layout, and the
pane's focus proxy/Tab handling are re-pointed at it the same way.

## Implementation

- `src/main/resources/base/Plugins/Core/core/imageviewer.py`:
  - `IMAGE_EXTENSIONS` / `is_image(url)` — the extension check that routes
    "View file" to this viewer instead of the text viewer (pure, unit
    tested).
  - `PaneImageView(QScrollArea)` — the viewer widget: a `QLabel` inside a
    `QScrollArea` (for panning when zoomed in). Loads a static image via
    `QPixmap`, or a `.gif` via `QMovie` (started immediately so it
    animates). `keyPressEvent` mirrors `PaneTextView`'s: Ctrl+Shift+P opens
    its own palette, a zoom-shortcut match (via
    `core.textviewer_zoom.zoom_delta_for`, reused rather than duplicated)
    rescales, then a `_bindable_commands()` lookup (via
    `core.key_bindings.command_for_key_event` — see "Bindable commands"
    above, against `Viewer Key Bindings.json`) is checked before the
    hardcoded Escape/Enter/Backspace close and Tab/Backtab switch-panes
    fallbacks, so a rebind always wins; everything else (arrow keys) falls through to
    `QScrollArea`'s own panning. `resizeEvent` re-fits while in fit mode.
  - `show_image_viewer(pane, url)` — mirrors `show_text_viewer`: mounts via
    `core/textviewer_pane.py`'s `begin_new_view`/`mount_view`, same as the
    text viewer.
- `src/main/resources/base/Plugins/Core/core/imageviewer_zoom.py` — the
  viewer's scale persistence, mirroring `core/textviewer_zoom.py`'s
  font-size persistence but for a multiplicative scale factor (own settings
  key `image_viewer_zoom` in `Core Settings.json` via `core/settings.py`):
  `get_saved_scale`, `save_scale` (`None` clears → fit mode), `clamp_scale`,
  `change_image_scale` (steps by ×1.25 per zoom delta, clamped to
  0.1–10.0), `reset_image_scale`. Reuses `zoom_delta_for` from
  `core/textviewer_zoom.py` rather than duplicating the keystroke-matching
  logic.
- `src/main/resources/base/Plugins/Core/core/textviewer_pane.py` —
  `confirm_close(view)` was generalized (one line) to tolerate a view with
  no `_editing` attribute of its own, via `getattr(view, '_editing',
  False)`, so an image view (always read-only) safely reports "fine to
  close" instead of raising `AttributeError`. The only change to code
  shared with the text viewer.
- `src/main/resources/base/Plugins/Core/core/commands/__init__.py` —
  `ViewFile.__call__` branches on `is_image(url)` after its existing
  exists/not-a-directory/local-file guards, calling `show_image_viewer`
  instead of `show_text_viewer` for image files; see
  [`docs/functions/view-file.md`](../functions/view-file.md).
- Tests:
  - `core/tests/test_imageviewer.py` — `is_image()`'s extension matching
    (case-insensitive, non-image rejected, no-extension rejected).
  - `core/tests/test_imageviewer_zoom.py` — `clamp_scale`'s bounds, and
    `change_image_scale`/`reset_image_scale`'s step/clamp/clear behaviour
    via injected `get_saved`/`save` fakes (so the math is tested without
    touching real settings I/O).
  - The remaining Qt-specific behaviour (actual paint/scaling, GIF
    animation, Tab/focus-proxy switching, the palette dialog, real
    scrollbar panning) was verified interactively, not unit-tested — same
    approach the text viewer takes (see
    [`docs/views/TEXT_VIEWER.md`](TEXT_VIEWER.md), Implementation section).
