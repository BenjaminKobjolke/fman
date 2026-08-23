# Open or view

Command that opens fman's internal viewer on the file under the cursor,
same as [`view_file`](view-file.md) — but falls back to
[`open`](../KEYBINDINGS.md) (OS default app, or navigate into the folder)
whenever the internal viewer can't handle the target, instead of showing
an alert. Meant to be bound to `Enter` for users who want the internal
viewer as their default open action without losing folder navigation or
having binaries (`.exe`, `.zip`, …) garbled by the text viewer.

## Usage

Not a default binding — opt in via your user `Key Bindings (<OS>).json`.
The typical setup swaps the default `Enter`/`Shift+Enter` roles:

```json
[{ "keys": ["Enter"], "command": "open_or_view" },
 { "keys": ["Shift+Enter"], "command": "open" }]
```

With this, `Enter` opens files in the internal viewer and still navigates
into folders; `Shift+Enter` becomes the normal OS-open action. See
[`docs/KEYBINDINGS.md`](../KEYBINDINGS.md#viewer-specific-bindings) for
the full opt-in section.

## Commands

| Command name  | Palette label / aliases                        | Default key binding |
|----------------|------------------------------------------------|----------------------|
| `open_or_view` | Open or view, Open (internal viewer for files)  | none (opt-in)        |

## Notes

- **Directory under cursor** → delegates to `open` (navigates in), same as
  pressing default `Enter`.
- **Viewable file under cursor** (image, video, or text — see
  [`view-file.md`](view-file.md#notes)) → delegates to `view_file`
  (internal viewer).
- **Binary/archive/executable, or a non-local path** → delegates to `open`
  (OS default app) instead of routing to the internal viewer, so `.exe`,
  `.zip`, and similar files never end up garbled in the text viewer.
- **Nothing under cursor** → delegates to `open` (its own no-op/handling).

## Implementation

- `src/main/resources/base/Plugins/Core/core/commands/__init__.py` —
  `OpenOrView` (`DirectoryPaneCommand`). Checks `is_dir`, the URL scheme,
  and `_is_viewable` (shared with `ViewFile`) on the file under the
  cursor, then routes via `self.pane.run_command('view_file')` or
  `self.pane.run_command('open')` — no duplicated open/view logic.
- See [`docs/functions/view-file.md`](view-file.md) for what `view_file`
  does once delegated to, including how it now refuses binaries itself.
