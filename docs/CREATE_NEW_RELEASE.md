# Creating a New Release

fman is built with **fbs** (fman build system — yes, the project that gave fbs its
name). `build.py` at the project root defines the fbs commands; `tools/*.bat` are
thin wrappers around `python build.py <command>`.

A release is identified by the label **`<version>_<build>`**, e.g. `1.7.5_3`:

- `version` (semver) — `src/build/settings/base.json`, key `"version"`. Bump by hand
  for feature/breaking changes.
- `build` (integer) — `build_version.txt` at the project root. Counter = the **last
  shipped** build; `0` = nothing shipped yet under this system (bump-first,
  ship-next).

## 1. Version & build number

```bat
tools\version_get.bat       :: prints <version>_<build>, e.g. 1.7.5_3
tools\build_get.bat         :: prints the current (last shipped) build number
tools\build_increment.bat   :: bump build before authoring a new release's notes
tools\build_decrement.bat   :: undo an increment
```

All four are thin wrappers over `tools\release\build_number.py` (plain `python`,
no `uv` — this project uses `requirements/*.txt`, not a `pyproject.toml`/uv
environment). Bump the semver `version` in `src/build/settings/base.json` by hand;
the build number is the only thing the bats manage.

Author release notes for the **next** label = `<version>_<build_get + 1>`. The
increment itself happens via `tools\build_increment.bat` as part of cutting the
release (step 4) — don't increment twice.

## 2. Release notes directory + `en.json` schema

Create `release_notes/<version>_<build>/en.json`:

```json
{
  "version": "1.7.5",
  "build": 3,
  "date": "YYYY-MM-DD",
  "title": "Short headline",
  "notes": [
    "First user-facing change",
    "Second user-facing change"
  ]
}
```

The actual release text is the **`notes`** array. **Author only `en.json`** — every
other locale is machine-generated (step 3). Do not hand-write any other locale
file.

## 3. Translate (mandatory — do not skip)

Run the project's translator wrapper to generate every other configured locale
from `en.json`:

```bat
tools\translate_release_notes.bat
```

This calls the shared **GPT-json-translator** tool
(`d:\GIT\BenjaminKobjolke\GPT-json-translator`) in recursive mode over the whole
`release_notes\` tree — it fills in only the missing/changed keys for each
`<version>_<build>\` folder that has an `en.json`, so it's safe to re-run any
time. Skipping this step means non-English users see no release notes (or stale
ones) for that release.

## 4. Build the release

```bat
tools\build_increment.bat        :: bump build_version.txt to the number you just authored notes for
tools\build_windows.bat          :: python build.py freeze  -> target\fman\
tools\build_windows_installer.bat:: python build.py installer -> target\fmanSetup.exe (fbs's own NSIS template)
```

`build.py` also exposes the full fbs pipeline for an actual public release:

```bat
python build.py release
```

This bumps `src/build/settings/base.json` to the release version, runs
`publish()` (`freeze` → `sign` → `installer` → `sign_installer` → `upload`), tags
the commit `v<version>` in git, bumps the settings file again for the next
`-SNAPSHOT` dev cycle, and pushes. `installer()` on Windows still comes from fbs
itself (fbs's built-in `Installer.nsi` template under
`fbs/_defaults/src/installer/windows/`) — there is no separate project-owned
installer config to maintain; override `src/installer/windows/Installer.nsi` in
this repo only if the installer needs to differ from fbs's default.

### Signing — XIDA network-share handshake, not fbs's local cert

`sign()` and `sign_installer()` are **overridden** in
`src/build/python/build_impl/windows.py` (imported into `build.py` in place of
fbs's own `fbs.builtin_commands.sign`/`sign_installer`). Reason: fbs's built-in
Windows signing uses a local `signtool` + `src/sign/windows/certificate.pfx`,
and that certificate (`CN=Michael Herrmann`, issued by Sectigo) **expired
2022-07-03** — it can no longer sign anything.

The overridden `sign()`/`sign_installer()` instead call `tools\sign_exe.bat`,
which reuses this org's shared `release-tool` signing handshake
(`D:\GIT\BenjaminKobjolke\release-tool`, `release_tool.pre_signer.PreSigner`):

1. Copies the exe to `\\XIDA-SERVER\SigningExecutables\`.
2. Polls `\\XIDA-SERVER\SigningExecutables\signed\` until the same filename
   appears there, signed by an external signing service watching that share.
3. Verifies the signer's certificate `CN` is `XIDA GmbH`.
4. Copies the signed file back over the original, cleans up both network
   locations.

Requires `uv` on PATH and access to the `release-tool` repo/network share — the
same prerequisites every other XIDA project's `sign_exe.bat` already assumes.
Order matters and is preserved from fbs's original `publish()`: the app exe
(`target/fman/fman.exe`) is signed **before** `installer()` packages it into
`fmanSetup.exe`, and the installer exe is signed **after**.

`tools\build_windows.bat` / `tools\build_windows_installer.bat` (freeze/installer
only, no signing) remain unsigned local test builds — only `python build.py
publish`/`release` produces a signed, shippable build.

**Housekeeping not yet done:** the dead cert (`src/sign/windows/certificate.pfx`)
and its password (`windows_sign_pass` in `src/build/settings/windows.json`) are
still committed and tracked in git history, along with other secrets in
`src/build/settings/base.json` (AWS keys, GPG passphrase, server API secret).
Nothing in this repo calls `fbs`'s signing path anymore, so these are now inert,
but they remain exposed in history. Rotate anything still live and consider
purging history if this repo is or was ever public.

**`release_notes/` is bundled into the frozen app.** fbs auto-bundles
everything under `src/main/resources/base/` into the frozen output
(`target/fman/`), but `release_notes/` lives at the project root (authored per
release, not under `src/main/resources`), so it needs an explicit copy.
`freeze()` in `src/build/python/build_impl/windows.py` copies it to
`target/fman/release_notes/` via `_copy_release_notes()`, next to the existing
`_copy_winpty_files()` step — skipped entirely if no release has been authored
yet. `core.release_notes.release_notes_dir()` (Core plugin) finds it there at
runtime, or falls back to the project-root `release_notes/` when running from
source before any freeze.

## 5. In-app Release Notes view

See [`docs/views/RELEASE_NOTES.md`](views/RELEASE_NOTES.md) for full usage
and implementation details. Summary:

Command **"Release Notes"** (`core/commands/release_notes.py`,
`ShowReleaseNotes`), invokable from the command palette. Lists every release
in `release_notes/`, newest first, via the palette's quicksearch UI; picking
one renders that release's notes read-only in the pane's text viewer
(`show_text_in_viewer`, see `docs/views/TEXT_VIEWER.md`). Hidden
(`is_visible()`) when no `release_notes/` folder is bundled.

Locale is detected via `python_localization.detection.detect_system_language`
(the `python-localization` dependency in `requirements/base.txt`), falling
back to `en.json` when a release has no translation for the detected locale,
or when the library itself is missing (defensive `ImportError` catch — Core's
other commands must still load even if this one dependency is broken).
Parsing/sorting/locale-fallback logic lives in `core/release_notes.py`
(pure, unit-tested — see `core/tests/test_release_notes.py`).
