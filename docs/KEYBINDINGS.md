# Key bindings

Reference for fman's default keyboard shortcuts and how to add or change
your own.

## Files and load order

fman merges key bindings from several `Key Bindings.json` files, each
optional, in this order (first match for a key wins —
`Controller.handle_shortcut`,
`src/main/python/fman/impl/controller.py:35-44`):

1. `Plugins/Core/Key Bindings.json` — base bindings (all platforms).
2. `Plugins/Core/Key Bindings (Windows|Mac|Linux).json` — platform-specific
   additions/overrides, checked *before* the base file.
3. `%APPDATA%/fman/Plugins/User/Settings/Key Bindings (Windows).json`
   (Windows; equivalent per-OS `Plugins/User/Settings/` folder elsewhere) —
   **the user override file**. This is the one you edit to customize a
   running install; it takes precedence over both Core files.

A binding entry is a JSON object:

```json
{ "keys": ["Ctrl+Shift+P"], "command": "command_palette" }
```

`keys` is a one-element array holding the shortcut string (`+`-joined
modifiers); `command` is the lowercased command name. Some commands take an
extra `args` object, e.g.:

```json
{ "keys": ["Alt+F1"], "command": "show_volumes", "args": {"pane_index": 0} }
```

To add your own binding, edit (or create) your user
`Key Bindings (<OS>).json` and add an entry to the top-level array — it
doesn't need to repeat anything from the Core files, only what you're adding
or overriding.

## Default bindings — base (all platforms)

| Keys | Command |
|------|---------|
| `Down` / `Num+Down` | `move_cursor_down` |
| `Shift+Down` | `move_cursor_down` (extends selection) |
| `Up` / `Num+Up` | `move_cursor_up` |
| `Shift+Up` | `move_cursor_up` (extends selection) |
| `Home` / `Num+Home` | `move_cursor_home` |
| `Shift+Home` | `move_cursor_home` (extends selection) |
| `End` / `Num+End` | `move_cursor_end` |
| `Shift+End` | `move_cursor_end` (extends selection) |
| `PgDown` / `Num+PgDown` | `move_cursor_page_down` |
| `Shift+PgDown` | `move_cursor_page_down` (extends selection) |
| `PgUp` / `Num+PgUp` | `move_cursor_page_up` |
| `Shift+PgUp` | `move_cursor_page_up` (extends selection) |
| `Space` | `toggle_selection` |
| `Tab` | `switch_panes` |
| `Backspace` | `go_up` |
| `Enter` | `open` (navigate into folders, OS-open files) |
| `F1` | `help` |
| `F4` | `open_with_editor` |
| `Shift+F4` | `create_and_edit_file` |
| `F5` | `copy` |
| `Shift+F5` | `symlink` |
| `Shift+F6` | `rename` |
| `F6` | `move` |
| `F7` | `create_directory` |
| `F8` / `Delete` / `Num+Delete` | `move_to_trash` |
| `F9` | `open_terminal` |
| `F10` | `open_native_file_manager` |
| `F11` | `copy_paths_to_clipboard` |
| `Shift+Delete` | `delete_permanently` |
| `Alt+F1` | `show_volumes` (left pane) |
| `Alt+F2` | `show_volumes` (right pane) |
| `Num+Insert` | `move_cursor_down` (extends selection) |
| `Alt+Up` | `increase_pane_font_size` |
| `Alt+Down` | `decrease_pane_font_size` |

## Windows additions

| Keys | Command |
|------|---------|
| `Ctrl+Right` | `open_in_right_pane` |
| `Ctrl+Left` | `open_in_left_pane` |
| `Ins` | `move_cursor_down` (extends selection) |
| `Ctrl+C` | `copy_to_clipboard` |
| `Ctrl+X` | `cut` |
| `Ctrl+V` | `paste` |
| `Ctrl+A` | `select_all` |
| `Ctrl+D` | `deselect` |
| `Ctrl+.` | `toggle_hidden_files` |
| `Ctrl+P` | `go_to` |
| `Ctrl+Shift+P` | `command_palette` |
| `Alt+Left` | `go_back` |
| `Alt+Right` | `go_forward` |
| `Alt+F5` | `pack` |
| `Ctrl+R` | `reload` |
| `Ctrl+F1`/`F2`/`F3` | `sort_by_column` (name/size/date) |
| `Ctrl+Up` | `go_up` |
| `Alt+Enter` | `show_explorer_properties` |
| `Ctrl+\` | `go_to_root_of_current_drive` |

## macOS additions

| Keys | Command |
|------|---------|
| `Alt+Right` | `open_in_right_pane` |
| `Alt+Left` | `open_in_left_pane` |
| `Cmd+C` | `copy_to_clipboard` |
| `Cmd+X` | `cut` |
| `Cmd+V` | `paste` |
| `Cmd+Alt+V` | `paste_cut` |
| `Cmd+A` | `select_all` |
| `Cmd+D` | `deselect` |
| `Space` | `move_cursor_down` (extends selection) |
| `Cmd+Backspace` | `move_to_trash` |
| `Cmd+.` | `toggle_hidden_files` |
| `Cmd+P` | `go_to` |
| `Cmd+Shift+P` | `command_palette` |
| `Cmd+Left` | `go_back` |
| `Cmd+Right` | `go_forward` |
| `Cmd+I` | `get_info` |
| `Cmd+F5` | `pack` |
| `Cmd+R` | `reload` |
| `Cmd+F1`/`F2`/`F3` | `sort_by_column` (name/size/date) |
| `Cmd+M` | `minimize` |
| `Cmd+Q` | `quit` |
| `Cmd+Up` | `go_up` |
| `Shift+Space` | `quick_look` |
| `Cmd+Enter` | `open_selected_files` |
| `Cmd+Ctrl+F` | `toggle_fullscreen` |

## Linux additions

| Keys | Command |
|------|---------|
| `Ctrl+Right` | `open_in_right_pane` |
| `Ctrl+Left` | `open_in_left_pane` |
| `Ins` | `move_cursor_down` (extends selection) |
| `Ctrl+C` | `copy_to_clipboard` |
| `Ctrl+X` | `cut` |
| `Ctrl+V` | `paste` |
| `Ctrl+A` | `select_all` |
| `Ctrl+D` | `deselect` |
| `Ctrl+.` | `toggle_hidden_files` |
| `Ctrl+P` | `go_to` |
| `Ctrl+Shift+P` | `command_palette` |
| `Ctrl+Q` | `quit` |
| `Alt+Left` | `go_back` |
| `Alt+Right` | `go_forward` |
| `Alt+F5` | `pack` |
| `Ctrl+R` | `reload` |
| `Ctrl+F1`/`F2`/`F3` | `sort_by_column` (name/size/date) |
| `Ctrl+Up` | `go_up` |

## Viewer-specific bindings

The [text viewer](views/TEXT_VIEWER.md) and
[image viewer](views/IMAGE_VIEWER.md) only bind a few keys directly (the
rest fall through to text navigation/selection, or panning for images):

| Keys | Effect |
|------|--------|
| `Escape` / `Enter` / `Backspace` | Close the viewer, return to the file list |
| `Tab` / `Shift+Tab` | Switch panes (same as the file list) |
| `Ctrl+Shift+P` | Open the viewer's own command palette (exit/edit/save, zoom) |
| Whatever `increase_pane_font_size`/`decrease_pane_font_size` are bound to (`Alt+Up`/`Alt+Down` by default) | Zoom the viewer's text/image |

`view_file` (opens the internal viewer on the file under the cursor — see
[`docs/functions/view-file.md`](functions/view-file.md)) ships with **no
default binding**, precisely so it doesn't change what Enter/double-click
do. To open it with a key of your own, add it to your user
`Key Bindings (<OS>).json`, e.g. bind it to `Shift+Enter`:

```json
{ "keys": ["Shift+Enter"], "command": "view_file" }
```

Note this only opens the viewer — it doesn't replace `Enter`'s normal
behaviour (navigate into folders / OS-open files), and it will show an
alert if used on a directory or a non-local path.

If you want the internal viewer to be your *default* action on `Enter`
instead — e.g. you view files more often than you OS-open them — bind
`Enter` to [`open_or_view`](functions/open-or-view.md) instead of
`view_file` directly. Unlike `view_file`, `open_or_view` falls back to
`open` (navigate in) when the cursor is on a directory, so folder
navigation keeps working:

```json
[{ "keys": ["Enter"], "command": "open_or_view" },
 { "keys": ["Shift+Enter"], "command": "open" }]
```

With this, `Enter` opens files in the internal viewer and still navigates
into folders; `Shift+Enter` becomes the normal OS-open action.
