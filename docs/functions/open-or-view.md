# Open or view

Command that opens fman's internal viewer on the file under the cursor,
same as [`view_file`](view-file.md) — but falls back to
[`open`](../KEYBINDINGS.md) (navigate into the folder) when the cursor is
on a directory, instead of showing an alert. Meant to be bound to `Enter`
for users who want the internal viewer as their default open action
without losing folder navigation.

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
- **File under cursor** → delegates to `view_file` (internal viewer);
  inherits its guards (non-local paths show an alert, image vs. text
  routing).
- **Nothing under cursor** → delegates to `open` (its own no-op/handling).
- `view_file` itself is unchanged — running it from the palette on a
  directory still shows "Cannot view a directory."

## Implementation

- `src/main/resources/base/Plugins/Core/core/commands/__init__.py` —
  `OpenOrView` (`DirectoryPaneCommand`). Checks `is_dir` on the file under
  the cursor and routes via `self.pane.run_command('view_file')` or
  `self.pane.run_command('open')` — no duplicated open/view logic.
- See [`docs/functions/view-file.md`](view-file.md) for what `view_file`
  does once delegated to.
