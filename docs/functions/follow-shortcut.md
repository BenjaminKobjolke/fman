# Follow shortcut

Windows only. With the cursor on a `.lnk` shortcut, navigates the pane to the
shortcut's destination instead of launching it:

- **Destination is a folder** → the pane opens that folder.
- **Destination is a file** → the pane opens the file's folder and puts the
  cursor on the file.

## Usage

Open the command palette (`Ctrl+Shift+P`) on a shortcut and pick **Follow
shortcut**. The entry is only listed while the cursor is on a local `.lnk`
file (any case — `.LNK` counts).

No default key binding. To add one, in your user `Key Bindings (Windows).json`:

```json
{ "keys": ["Ctrl+L"], "command": "follow_shortcut" }
```

## Commands

| Command name      | Palette label   | Keywords                                                                   | Default key binding |
|-------------------|-----------------|----------------------------------------------------------------------------|---------------------|
| `follow_shortcut` | Follow shortcut | lnk, shortcut, link target, destination, go to destination, go to target   | none                |

The words listed under *Keywords* are hidden search terms: they find the
command in the palette without ever being shown. See
[the command palette](../COMMAND_PALLETTE.md#hidden-search-keywords).

## Enter versus Follow shortcut

| Shortcut points at | `Enter` (`open`)        | Follow shortcut                         |
|--------------------|-------------------------|-----------------------------------------|
| a folder           | opens the folder        | opens the folder                        |
| a file             | Windows launches it     | opens its folder, cursor on the file    |
| nothing reachable  | Windows reports the error | alert: destination does not exist     |

## Notes

- Some shortcuts have no file system destination at all — "advertised"
  shortcuts written by MSI installers, and shortcuts into the shell namespace
  (Control Panel items, *This PC*). Windows reports an empty target for them,
  so Follow shortcut shows the "does not exist" alert. `Enter` still launches
  them.
- The shortcut's arguments and working directory are ignored; only its target
  path matters for navigation.
- Symbolic links and junctions are not shortcuts: fman already follows those
  when you open them.

## Implementation

- `src/main/resources/base/Plugins/Core/core/commands/navigation.py` —
  `FollowShortcut` (`DirectoryPaneCommand`), defined only on Windows. Hands the
  destination to `open_directory`, which already knows "folder → open it,
  file → open the parent and place the cursor".
- `src/main/resources/base/Plugins/Core/core/commands/util.py` —
  `is_shortcut` and `shortcut_target` (`WScript.Shell` via pywin32). Shared with
  `_open_local_files_win` in `opening.py`, which is why `Enter` and this command
  cannot disagree about where a shortcut points.
