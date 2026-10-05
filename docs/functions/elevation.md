# Administrator rights (UAC) for protected folders

fman runs without administrator rights. When a file operation targets a
folder that needs them — `C:\Program Files\…`, `C:\Windows\…` — fman hands
that one operation to Windows, which shows the usual UAC prompt and carries
it out. fman itself stays unelevated: programs you start from it, drag and
drop and network drives all keep working as before.

Windows only, local files (`file://`) only.

## Usage

Nothing to learn — use the normal commands. In a protected folder they raise
one UAC prompt per operation:

| Command                       | In a protected folder                        |
|-------------------------------|----------------------------------------------|
| New file (`Shift+F4`)         | UAC prompt, file is created, editor opens    |
| New folder (`F7`)             | UAC prompt, folder is created                |
| Copy (`F5`), paste, drag-drop | UAC prompt, Windows' own copy dialog         |
| Move (`F6`), cut and paste    | UAC prompt, Windows' own move dialog         |
| Rename (`F2`)                 | UAC prompt                                   |
| Delete, Delete permanently    | UAC prompt (after fman's own confirmation)   |

Declining the prompt cancels the operation. New file and New folder then say
*"You do not have enough permissions to create …"*; the others do nothing.

## Notes

- **Windows' dialogs, not fman's.** An elevated copy or move is performed by
  the Windows shell, exactly as in Explorer. Progress, "replace or skip" and
  folder-merge questions therefore come from Windows for that operation.
  Everywhere else you still get fman's own dialogs.
- **One prompt for the whole selection.** Copying 50 files asks once.
- **Moving out counts too.** Moving a file *out of* a protected folder needs
  rights there (the source is removed), so it is elevated as well. Copying
  out is not — reading needs no rights.
- **A destination folder that does not exist yet** inside a protected folder
  is created first, with a UAC prompt of its own — so two prompts. Likewise
  New folder with a nested name (`a\b`) asks once per missing level.
- **A single locked file in a normal folder** is not covered: the check is
  per folder. Such a file fails as it did before.
- **Saving from an editor** is the editor's business. A file opened from a
  protected folder still cannot be saved unless the editor elevates itself.
- **Not in archives or on network locations** — other file systems are
  untouched.

## Implementation

`src/main/resources/base/Plugins/Core/core/elevation.py`.

- **Deciding** — `needs_elevation(*dir_urls)` creates and immediately removes
  a temporary file (`O_TEMPORARY`) in each directory, or in its nearest
  existing ancestor. `PermissionError` means protected. The decision is made
  *before* the operation rather than by catching `PermissionError` during
  it, for two reasons: fman's own copy/move/delete works file by file, which
  would mean one UAC prompt per file; and a file held open by another
  program raises `PermissionError` too, for which [rename](rename.md)'s
  Retry is the right answer, not a UAC prompt.

  `tempfile` is deliberately not used for the probe: on Windows it answers
  `PermissionError` with thousands of retries under other names.
- **Doing** — `copy`, `move`, `delete`, `rename` and `create` each queue their
  items on one `IFileOperation` (pywin32's `win32com.shell`) and `_perform`
  runs it with `FOFX_SHOWELEVATIONPROMPT`. The first four return whether they
  handled the operation; `False` tells the caller to carry on as usual.
  `create` is the fallback for after a plain attempt failed and returns
  whether the item now exists.
- **Refreshing** — fman does not watch directories on Windows, so `_notify`
  reports the top-level items to `fman.fs.notify_file_added` /
  `notify_file_removed`, each guarded by a check on disk: the user may have
  declined, canceled halfway or skipped files in Windows' dialog.

The callers, all under `core/commands/`:

| File          | Where                                             |
|---------------|---------------------------------------------------|
| `transfer.py` | `_TreeCommand.__call__` via `Copy`/`Move._call_elevated` |
| `deletion.py` | `trash()` and `DeletePermanently`                  |
| `rename.py`   | `rename_to()`; `CreateDirectory` on `PermissionError` |
| `editor.py`   | `CreateAndEditFile` on `PermissionError`           |
| `util.py`     | `create_as_admin()` — shared by the two create commands |

Tests: `core/tests/test_elevation.py` covers the probe, what each operation
queues (with `_perform` replaced) and that every command hands over or
carries on. The UAC prompt itself cannot be automated; see the manual
checklist in `claude-plans/i-cant-copy-reactive-grove.md`.
