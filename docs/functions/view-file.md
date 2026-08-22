# View file

Command palette entry that opens fman's internal text viewer on the
file under the cursor, showing its contents inside the active pane instead
of launching an external application.

See [`docs/views/TEXT_VIEWER.md`](../views/TEXT_VIEWER.md) for how the
viewer itself behaves (navigation, size limits, encoding, closing).

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
- Running it with nothing under the cursor shows "No file is selected!".

## Implementation

- `src/main/resources/base/Plugins/Core/core/commands/__init__.py` —
  `ViewFile` (`DirectoryPaneCommand`). Validates the file under the cursor
  (exists, not a directory, local `file://` scheme) and then calls
  `show_text_viewer(self.pane, url)`.
- `src/main/resources/base/Plugins/Core/core/textviewer.py` — the viewer
  itself (`show_text_viewer`, `PaneTextView`); see
  [`docs/views/TEXT_VIEWER.md`](../views/TEXT_VIEWER.md) for details.
