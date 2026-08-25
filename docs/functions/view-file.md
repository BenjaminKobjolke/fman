# View file

Command palette entry that opens fman's internal viewer on the file under
the cursor, showing its contents inside the active pane instead of
launching an external application. Image files (`.png`, `.jpg`, `.jpeg`,
`.gif`, `.bmp`, `.webp`, `.ico`, `.svg`) open the
[image viewer](../views/IMAGE_VIEWER.md); video files (`.mp4`, `.m4v`,
`.mkv`, `.webm`, `.avi`, `.mov`, `.wmv`, `.flv`, `.mpg`, `.mpeg`, `.ogv`,
`.3gp`, `.ts`) open the [video viewer](../views/VIDEO_VIEWER.md); everything
else is sniffed for binary content — text-like files open the
[text viewer](../views/TEXT_VIEWER.md), binaries (`.exe`, `.zip`, and
similar) show an alert instead of being rendered as garbage.

See [`docs/views/TEXT_VIEWER.md`](../views/TEXT_VIEWER.md),
[`docs/views/IMAGE_VIEWER.md`](../views/IMAGE_VIEWER.md), and
[`docs/views/VIDEO_VIEWER.md`](../views/VIDEO_VIEWER.md) for how each
viewer behaves.

## Usage

1. Put the cursor on a file.
2. Open the command palette and search "view" (or "internal viewer") and
   run **"View file"**.
3. The file's contents fill the active pane. Press Escape, Enter, or
   Backspace to close it and return to the file list — or press
   **Ctrl+Shift+P** for the viewer's own command palette (exit/edit/save;
   see [`docs/views/TEXT_VIEWER.md`](../views/TEXT_VIEWER.md#editing)).

## Commands

| Command name | Palette label / aliases          | Default key binding |
|--------------|-----------------------------------|----------------------|
| `view_file`  | View file, View, Internal viewer  | none (palette only)  |
| `view_file_in_other_pane` | View file in other pane, View in other pane | none (palette only) |

Both can be bound to a key in `Key Bindings.json` like any other command, e.g.:

```json
{ "keys": ["Ctrl+Alt+V"], "command": "view_file" }
```

`view_file_in_other_pane` opens the same viewer for the file under the cursor
but mounts it in the **other** pane, so the current pane's file list stays
visible for previewing side by side. Keyboard focus deliberately stays in the
current pane, so you can keep moving the cursor through the folder and preview
each file in the other pane as you go. With only one pane open it falls back to
viewing in place (and there the viewer takes focus as usual).

## Notes

- **Enter/double-click are unaffected.** This command is a separate,
  palette-only path — pressing Enter or double-clicking a file still opens
  it with the OS default application, exactly as before.
- Running the command on a directory, or on a non-local (non-`file://`)
  path, shows an alert instead of opening the viewer.
- Running it on a binary file (anything that isn't an image, video, or
  text — the check reads a chunk of the file and looks for a NUL byte)
  shows an alert instead of dumping garbled bytes into the text viewer.
- Running it with nothing under the cursor shows "No file is selected!".
- **Next / previous file** inside an open viewer re-runs `view_file` under the
  hood: it steps the pane cursor to the neighbouring file and re-routes to the
  matching viewer. See
  [File viewers](../viewers/FILE_VIEWERS.md#shared-behaviour).

## Implementation

- `src/main/resources/base/Plugins/Core/core/commands/__init__.py` —
  `ViewFile` (`DirectoryPaneCommand`). Validates the file under the cursor
  (exists, not a directory, local `file://` scheme), then routes on
  `is_image(url)`/`is_video(url)`/`is_text_file(...)`: image files call
  `show_image_viewer(self.pane, url)`, video files
  `show_video_viewer(self.pane, url)`, text-like files
  `show_text_viewer(self.pane, url)`, anything else shows an alert.
  `_is_viewable(url)` in the same module exposes this same check for
  [`OpenOrView`](open-or-view.md) to pre-filter before delegating here.
  `is_text_file` lives in `core/textviewer_io.py`. The validate+route body is
  factored into the module-level
  `_view_file_in(source_pane, target_pane, focus_view=True)` helper; `ViewFile`
  calls it with the active pane as both source and target, while
  `ViewFileInOtherPane` (`view_file_in_other_pane`) passes
  `_get_opposite_pane(self.pane)` as the target with `focus_view=False` so the
  viewer mounts in the other pane without stealing keyboard focus (the
  `focus_view` flag is threaded through `show_*_viewer` down to `mount_view`).
  When `focus_view=False`, `mount_view` doesn't just skip its deferred
  `view.setFocus()` — merely mounting the viewer still blurs the source pane's
  file list, so it actively re-focuses the *opposite* pane (the one the command
  ran from) on the same deferred tick to win over that blur. With one pane open
  the target is the active pane, so `focus_view` is `True` and it behaves like
  `ViewFile`.
- `src/main/resources/base/Plugins/Core/core/textviewer.py` — the text
  viewer (`show_text_viewer`, `PaneTextView`); see
  [`docs/views/TEXT_VIEWER.md`](../views/TEXT_VIEWER.md) for details.
- `src/main/resources/base/Plugins/Core/core/imageviewer.py` — the image
  viewer (`is_image`, `show_image_viewer`, `PaneImageView`); see
  [`docs/views/IMAGE_VIEWER.md`](../views/IMAGE_VIEWER.md) for details.
- `src/main/resources/base/Plugins/Core/core/videoviewer.py` — the video
  viewer (`is_video`, `show_video_viewer`, `PaneVideoView`); see
  [`docs/views/VIDEO_VIEWER.md`](../views/VIDEO_VIEWER.md) for details.
- `src/main/resources/base/Plugins/Core/core/viewer_navigation.py` — shared
  next/previous-file navigation (`advance` re-runs this command via
  `pane.run_command('view_file')`) and the per-viewer "advance only for same
  type" toggle; see [`docs/views/IMAGE_VIEWER.md`](../views/IMAGE_VIEWER.md#implementation).
