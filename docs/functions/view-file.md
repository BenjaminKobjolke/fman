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

Can be bound to a key in `Key Bindings.json` like any other command, e.g.:

```json
{ "keys": ["Ctrl+Alt+V"], "command": "view_file" }
```

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
  `is_text_file` lives in `core/textviewer_io.py`.
- `src/main/resources/base/Plugins/Core/core/textviewer.py` — the text
  viewer (`show_text_viewer`, `PaneTextView`); see
  [`docs/views/TEXT_VIEWER.md`](../views/TEXT_VIEWER.md) for details.
- `src/main/resources/base/Plugins/Core/core/imageviewer.py` — the image
  viewer (`is_image`, `show_image_viewer`, `PaneImageView`); see
  [`docs/views/IMAGE_VIEWER.md`](../views/IMAGE_VIEWER.md) for details.
- `src/main/resources/base/Plugins/Core/core/videoviewer.py` — the video
  viewer (`is_video`, `show_video_viewer`, `PaneVideoView`); see
  [`docs/views/VIDEO_VIEWER.md`](../views/VIDEO_VIEWER.md) for details.
