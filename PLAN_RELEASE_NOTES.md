# Plan: In-App Release Notes View

Not implemented yet. Overview for a future session to pick up.

## Goal

A command that opens a dialog showing release notes, newest release first, with
Older/Newer navigation between releases. Falls back to `en.json` when the user's
locale file is missing for a given release.

## Where it plugs in

fman is command-driven (Sublime-Text-style command palette), not a traditional
menu bar. New commands live in
`src/main/resources/base/Plugins/Core/core/commands/`. Existing examples to
follow the pattern of:

- `core/commands/__init__.py` — defines `ApplicationCommand` /
  `DirectoryPaneCommand` base classes; a release-notes command is global (not
  file/pane-scoped), so it should be an `ApplicationCommand`.
- `core/commands/explorer_properties.py` — example `DirectoryPaneCommand` with
  `aliases = (...)` and `is_visible()`.
- `core/textviewer.py` / `core/textviewer_io.py` / `core/textviewer_zoom.py`
  (see `docs/views/TEXT_VIEWER.md`) — most recent example of adding a new
  in-app view backed by its own module; good reference for dialog/widget
  structure and how a view command wires into the pane.

Prior art command names live in `core/commands/__init__.py` and
`core/commands/goto.py` for the alias/registration pattern (e.g. how a command
becomes invokable from the command palette).

## Data source

Reads bundled `release_notes/<version>_<build>/<locale>.json` (see
`docs/CREATE_NEW_RELEASE.md` section 4 — bundling into the frozen build is a
prerequisite, not yet done). At runtime:

1. List subfolders of the bundled `release_notes/` dir.
2. Parse `<version>_<build>` from each folder name to sort newest-first
   (numeric compare on `build`, not string sort — `10` must sort after `9`).
3. For the active UI locale, load `<locale>.json`; if missing, fall back to
   `en.json`.

## Dialog behavior

- Opens showing the newest release's `title` + `notes` bullets + `date`.
- "Older" / "Newer" buttons (or arrow keys) step through the sorted list;
  disable "Newer" at the newest entry and "Older" at the oldest.
- Simple `QDialog` + `QVBoxLayout` is enough — no need for a scrolling
  infinite-load list (this is a desktop file manager, not a mobile app; the
  full release history is small and can load eagerly).

## Command registration

- New file: `core/commands/release_notes.py`, class e.g. `ShowReleaseNotes`
  extending `ApplicationCommand`, with `aliases = ('Release Notes',)` (or
  similar — match the alias style used by other commands in the same
  directory).
- Decide entry point: command palette only, or also a Help-menu-equivalent
  (fman may have a Help/About command already — check `core/commands/` for one
  and place Release Notes as a sibling).

## Tests

Follow `CODING_RULES.md` TDD workflow: unit tests for the folder-parsing /
sort / locale-fallback logic (pure functions, easy to isolate from Qt), plus a
smoke test that the command is registered and `is_visible()` returns `True`
when `release_notes/` exists.

## Open questions for whoever implements this

- Confirm the exact bundling mechanism from `docs/CREATE_NEW_RELEASE.md`
  section 4 is done first (the view has nothing to read otherwise).
- Confirm whether fman already has a Help/About command to sit next to, or
  whether Release Notes is the first entry of its kind.
