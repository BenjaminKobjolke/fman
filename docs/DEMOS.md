# Recording demos

fman can record animated demos (GIF/MP4 + PNG stills) of its UI with the
[automated-application-screenshots](https://github.com/BenjaminKobjolke/automated-application-screenshots)
tool. The recorded demos are shown in the [README](../README.md#demo).

Recording the feature tour end to end is five commands (see
[Recording checklist](#recording-checklist)); the rest of this document is what
you need when a step doesn't do what you scripted.

## How it works

In demo mode fman plays a scripted sequence of UI actions and reports events
over a socket so the tool can capture the window. The wiring:

- `src/main/python/fman/impl/demo_scripts.py` — the `DEMOS` registry, one
  `DemoScript` per recordable demo.
- `src/main/python/fman/impl/demo.py` — the PyQt5 demo player that turns those
  scripts into key events.
- `src/main/python/fman/impl/application_context.py` — `run()` enters demo mode
  when `--automation-demo` is on the command line (`_run_demo()`), and skips the
  splash/tutorial and single-instance handoff so the recording is clean.
- `tools/create_media/fman.json` — the tool-side config (window size, formats,
  output folder).
- `tools/create_media/run_fman_demo.bat` — launcher the tool starts per run.
- `tools/demos_record.bat` — one command that drives the whole recording.
- `tools/create_media/build_tour.py` + `tools/demo_build_tour.bat` — join the
  recorded tour chapters into the README's feature-tour MP4.
- `tools/create_media/build_themes.py` + `tools/demo_themes_record.bat` — record
  one still per theme and join them into the README's themes GIF.

fman itself never captures or encodes anything. It only posts key events and
sends `demo_started` / `screenshot` / `demo_ended` over a socket; the tool grabs
the window region with pyautogui and writes the GIF/MP4.

### Panes and the demo profile

Demo 1 reads the committed `examples/left_pane` (images + a video) and
`examples/right_pane` (text/markdown). The tour chapters create, rename, move
and pack files, so `run_fman_demo.bat` gives every id ≥ 3 its own scratch
fixtures, wiped and re-seeded on each run:

| path | contents |
|------|----------|
| `%TEMP%\fman-demo-<id>-left` | both example folders merged — 11 images/video + 6 text files |
| `%TEMP%\fman-demo-<id>-right` | empty |
| `%TEMP%\fman-demo-profile` | the throwaway fman data directory |

Every run sets `FMAN_DATA_DIRECTORY` to that profile and wipes its `Plugins`
folder. Recording against your own profile would load your third-party plugins,
whose key bindings are prepended (so they beat Core's: `ArrowNavigation` takes
Left/Right, `fman-flatview` takes `Ctrl+F2`) and whose commands change what a
typed palette query resolves to — `compare`, for instance, stops meaning
`Compare directories`. It would also write viewer zoom and volume back into
your settings, so a second recording wouldn't match the first. Redirecting
`APPDATA` would isolate the same things, but that is also where `pip --user`
installs PyQt5 and fbs_runtime, hence fman's own override.

Two things are deliberately copied *in* from your real profile, because they
change how a recording looks rather than how it behaves:

- `Local\Settings.json` — your theme. Without it every demo records in the
  default Monokai. The `window_opacity` in that file has no effect: demo mode
  pins `DEMO_OPACITY` (`demo_scripts.py`) so every chapter starts at the same
  known value, whatever your profile or a previous take says.
- `%APPDATA%\fman\Themes` — mirrored so a *custom* theme resolves instead of
  silently falling back to the default.

The launcher also minimizes every window (`Shell.Application.MinimizeAll`) right
before starting fman. The recorder grabs screen pixels of fman's window rect, so
any window drawn over it — including the console the tool spawns per demo —
would land in the recording.

## Install (once)

Demo mode needs the app-side connector library. It is **not** in the normal
requirements — it lives in a dev-only file so it never enters a release build.
From the repo root:

    pip install -r requirements/windows-debug.txt

This installs [automated-screenshot-connector](https://github.com/BenjaminKobjolke/automated-application-screenshots-python-connector)
(expected as a sibling checkout: `../automated-application-screenshots-python-connector`).

The recording tool itself is a separate checkout and runs with
[uv](https://docs.astral.sh/uv/). Expected at
`../automated-application-screenshots` (edit `TOOL_DIR` in
`tools/demos_record.bat` if yours is elsewhere).

Joining the tour needs **ffmpeg** on `PATH`.

**The interpreter matters.** fman's dependencies (PyQt5, fbs_runtime) are a
`pip --user` install, and the connector is an editable `.pth` install — both
live in that interpreter's user site-packages, so another `python` on `PATH`
(msys2's, a venv) will fail with `ModuleNotFoundError: fbs_runtime`. Point
`FMAN_PYTHON` at the right `python.exe` if plain `python` isn't it:

    set FMAN_PYTHON=C:\Program Files\Python314\python.exe

(The launcher already drops the tool's own `uv` virtualenv from `PATH`.)

## Recording checklist

1. **Close every always-on-top desktop widget** (clock/system-monitor gadgets,
   notification toasts, anything pinned above other windows). The capture is a
   screen region, so whatever is drawn over fman is burned into every frame and
   no setting in the tool can exclude it.
2. **Check libmpv is cached** at
   `%TEMP%\fman-demo-profile\Local\libmpv\libmpv-2.dll` — the launcher copies it
   from your real profile. Without it the first video view downloads ~100 MB
   behind a progress dialog, on camera.
3. **Preview any script you changed** (see
   [Preview a demo](#preview-a-demo-without-the-tool)) and check its side
   effects; don't burn a recording on an unproven script.
4. **Record the chapters one at a time** so a misfire costs one clip, not five:

       tools\demos_record.bat --demo 3
       tools\demos_record.bat --demo 4
       tools\demos_record.bat --demo 5
       tools\demos_record.bat --demo 6
       tools\demos_record.bat --demo 7

5. **Join them:** `tools\demo_build_tour.bat` → `media/demos/tour/feature-tour.mp4`.
6. **Watch the result** before committing. The build prints the size; the last
   run was 2:32 and 2.3 MB.

`tools\demos_record.bat` with no arguments records every demo; any other
arguments pass straight through to the tool.

The themes GIF is its own one-liner, `tools\demo_themes_record.bat` — see
[The themes demo](#the-themes-demo).

## What ships

- **1 `overview`** — short; the four stills in the README feature grid
  (both panes, internal image viewer, inline filter, select-all). The only
  demo whose PNGs are committed - the themes demo's are an intermediate.
- **2 `themes`** — one still per bundled theme, joined into the README's
  `media/demos/themes/themes.gif`. Records no video at all.
- **3–7, the `tour-*` chapters** — the README's feature tour:

  | id | name | shows | measured |
  |----|------|-------|----------|
  | 3 | `tour-a-panes` | select, copy across panes, type-to-filter, sort | 302 frames, 30.2 s |
  | 4 | `tour-b-organize` | `F7` new folder, `F6` move, `Shift+F6` rename | 267 frames, 26.7 s |
  | 5 | `tour-c-viewers` | image viewer + zoom + next file, text viewer + edit/save | 328 frames, 32.8 s |
  | 6 | `tour-d-video` | video playing in the pane, and previewing into the other one | 276 frames, 27.6 s |
  | 7 | `tour-e-archives` | pack, browse inside the zip, copy out, fuzzy palette | 354 frames, 35.4 s |

The chapters exist because of hard limits in the recorder, not taste:

| limit | value | consequence |
|-------|-------|-------------|
| frames held in RAM | ~3 MB each at 1280x800, and the MP4 export copies them all again as numpy arrays | ~30 MB per second at 10 fps — a single 2.5-minute take needs gigabytes |
| `DEMO_CAP_S` | 300 s | a longer demo is aborted |
| `EVENT_TIMEOUT_S` | 60 s | 60 s with no `demo_started`/`screenshot`/`demo_ended` aborts the run. A chapter under a minute is covered by `demo_started` alone; a longer one needs `Screenshot` steps as heartbeats |
| `WINDOW_TIMEOUT_S` | 30 s | fman must show its window within 30 s of launch |

Output lands in `media/demos/<name>/` (see `output_dir` in
`tools/create_media/fman.json`): `demo.mp4`, plus `demo.gif` and one PNG per
`Screenshot` step if the demo asks for them. The tour chapters are `mp4` only —
a 2.5-minute GIF would be tens of megabytes for a worse picture.

`demo_build_tour.bat` burns each chapter's caption over its first 5 s and
concatenates all of them. Chapter order comes from `fman.json` (every demo whose
`name` starts with `tour-`, sorted by id), the caption text from `CAPTIONS` in
`build_tour.py` — add both when you add a chapter. It also rescales every input
to 1280 wide with `setsar=1`: the capture is the window *including* its frame
(1284x847 last time), and clips recorded in different sessions can differ by a
pixel, which plain `concat` rejects. Only the joined MP4 is committed — the
per-chapter `media/demos/tour-*/` folders are regenerable intermediates and
gitignored.

### The themes demo

Demo 2 is the only one whose steps are **built at run time**: `_run_demo`
passes `list_themes(bundled_theme_dirs)` to `build_themes_script`
(`demo_scripts.py`), which emits `Select theme` → `Screenshot(<name>)` per
theme. Add `Themes/Foo.json` and Foo is in the next recording — no edit to
`demo_scripts.py`, `fman.json` or `build_themes.py`.

Three things make it look nothing like the other demos:

| choice | why |
|--------|-----|
| `"formats": []` in `fman.json` | the tool then writes only the PNG stills, so the command palette it uses to switch themes never lands in the GIF — and the frames it holds in RAM are thrown away |
| `"fps": 2` | `Recorder.request_still` saves the *next captured* frame, so at 2 fps a still lands within 0.5 s of the event — inside the 1.2 s the script keeps the palette closed afterwards |
| **bundled** themes only | `theme_dirs` also holds the demo profile's `Themes`, which `run_fman_demo.bat` mirrors from `%APPDATA%` — so a repo asset would otherwise carry your private themes. Hence `bundled_theme_dirs` |

`build_themes.py` then joins `media/demos/themes/*.png` in name order (the
order `list_themes` returns) at `THEME_HOLD_S` per frame. It reads no theme
list of its own: the stills *are* the list. `demo_themes_record.bat` deletes them
first, so a theme you removed cannot linger in the GIF.

The one thing to check by eye: `Command(name)` types the theme's full name
into the quicksearch, which matches with `contains_chars`, so a short name is
a subsequence of a longer one (`Dark` also matches `Gruvbox Dark`). Ties break
by sorted order, which today always favours the exact name — but a future
theme sorting *before* one whose name it contains (`Ayu Dark` before `Dark`)
would steal the query and write the wrong picture under the right file name.

## Preview a demo without the tool

Fastest way to iterate on pacing — plays visually, records nothing, quits
itself:

    set PYTHONPATH=src\main\python
    set FMAN_DATA_DIRECTORY=%TEMP%\fman-demo-profile
    python src\main\python\fman\main.py --automation-demo 1 examples\left_pane examples\right_pane

For a tour chapter, pass its scratch folders instead (create them the way
`run_fman_demo.bat` does, or just run the chapter through the recorder once so
they exist).

**Check a chapter without watching it.** A preview leaves evidence: the files it
created, moved or renamed in the scratch folders, and the settings it persisted
in `%TEMP%\fman-demo-profile\Plugins\User\Settings\`. That is enough to prove
every risky step landed:

| chapter | proof it worked |
|---------|-----------------|
| 3 `tour-a-panes` | the right folder holds all 17 copies |
| 4 `tour-b-organize` | `documents/` exists and contains `history.txt` (renamed from `changelog.txt`) |
| 5 `tour-c-viewers` | `changelog.txt` ends with `Edited in fman` |
| 6 `tour-d-video` | `Core Settings (Windows).json` has `video_viewer_volume` — written only from the video viewer's own key handler, so it proves the viewer had keyboard focus |
| 7 `tour-e-archives` | `images.zip` in the left folder holds three JPEGs, and the right folder holds the one copied back out |

**Estimate a script's length** without running it:

    set PYTHONPATH=src\main\python
    python -c "from PyQt5.QtWidgets import QApplication; QApplication([]); from fman.impl.demo_scripts import DEMOS; from automated_screenshot_connector.steps import flatten; [print(s.name, sum(d for d,_ in flatten(s.steps))/1000, 's') for s in DEMOS.values()]"

Add ~1.5 s per chapter for the player's own start delay (500 ms) and end hold
(1000 ms).

## Writing a demo

### The steps

All from `automated_screenshot_connector`; `flatten()` expands them into timed
atomic actions, and the delay attached to each action elapses **before** it runs.

| step | expands to | notes |
|------|-----------|-------|
| `Pause(seconds)` | one no-op wait | the only way to give the UI time |
| `PressKey(chord)` | one key press+release after 60 ms | must be a single Qt chord (`'Ctrl+Shift+P'`, `'Down'`, `'Ins'`, `'Alt+F5'`) |
| `TypeText(text)` | one press+release per char, 60 ms apart, carrying the char as text | drives the inline filter and any focused `QLineEdit` |
| `Command(line)` | `TypeText(line)` + Return | **does not open the palette** — precede it with `PressKey('Ctrl+Shift+P')` |
| `Screenshot(name)` | a `screenshot` event after 400 ms of settle | writes `media/demos/<demo>/<name>.png` |

Player constants live in `demo.py`: `START_DELAY_MS = 500` before the first
action, `END_HOLD_MS = 1000` after the last one.

Events are posted to `QApplication.focusWidget()`, which is why they reach modal
dialogs and viewers as well as the file list. An unparsable chord is rejected
when the player is constructed, so a typo fails before the window is even
captured rather than minutes into a recording.

`TypeText` cannot carry a newline in fman — the library expands `'\n'` into a
plain character event, not a Return. Use `PressKey('Return')`.

### Pane order

`core.Name.get_sort_value` sorts directories first, then case-insensitively and
naturally. The seeded scratch folder is therefore always:

| row | file | row | file |
|-----|------|-----|------|
| 0 | `changelog.txt` | 9 | `dummy_6.jpg` |
| 1 | `config.json` | 10 | `dummy_7.jpg` |
| 2 | `data.csv` | 11 | `dummy_8.jpg` |
| 3 | `dummy.mp4` | 12 | `dummy_9.jpg` |
| 4 | `dummy_1.jpg` | 13 | `dummy_10.jpg` |
| 5 | `dummy_2.jpg` | 14 | `notes.md` |
| 6 | `dummy_3.jpg` | 15 | `readme.md` |
| 7 | `dummy_4.jpg` | 16 | `todo.txt` |
| 8 | `dummy_5.jpg` | | |

`dummy.mp4` precedes `dummy_1.jpg` because `.` sorts before `_`, and
`dummy_10.jpg` sorts after `dummy_9.jpg` because the comparison is natural, not
lexicographic. The cursor starts on row 0, so every `Down` count in a script is
written against this table — re-check them if the fixtures ever change.

### Palette queries

The global palette (`Ctrl+Shift+P`) matches in three tiers —
word-prefixes, then contained characters, then contained characters in any
order — takes each command's **first** matching alias, and sorts each tier by
title length, so the shortest matching command title wins. Verify a new query
against `core/commands/__init__.py` rather than guessing:

| query | resolves to | rival it beats |
|-------|-------------|----------------|
| `view file` | View file | `View file in other pane` |
| `view in other` | View file in other pane | — |
| `comp dir` | Compare directories | `Compare files` (a third-party command, absent from the demo profile but still a bad habit) |
| ~~`compare`~~ | ambiguous | picks `Compare files` when it exists |
| ~~`cd`~~ | **Move cursor down** | shorter title wins — not what you meant |
| ~~`cmp`~~ | **Compress...** | same trap |

A **viewer's own palette** (also `Ctrl+Shift+P`, handled inside the viewer
before the global one can see it) is simpler: single-tier character matching,
no sorting, first match in the viewer's action order wins. Verified queries:

| viewer | queries |
|--------|---------|
| image | `next`, `fit`, `zoom in`, `actual` |
| text (viewing) | `edit`, `exit`, `next` |
| text (editing) | `save`, `exit`, `revert` |
| video | `play`, `mute`, `restart`, `next`, `exit` |

### Dialogs and prompts

| command | what opens | prefill | confirm |
|---------|-----------|---------|---------|
| `F5` copy / `F6` move | a prompt | the other pane's path — **fully selected** for a multi-file selection, stem-only for a single file | Return. A bare name (no path) is resolved against the **source** pane |
| `F7` create folder | a prompt | the stem of the file under the cursor, fully selected | Return; the cursor is then placed on the new folder |
| `Shift+F6` rename | an **inline editor in the file list**, not a dialog | the stem, extension kept | Return. A path is rejected with an alert — type a bare name |
| `Alt+F5` pack | a prompt | `<other pane>\<name>.zip` with only the stem selected — press `Ctrl+A` first if you want to replace the whole path | Return |
| viewer *Save file* | **nothing** — writes straight to disk | — | — (*Save file as…* would prompt; avoid it) |
| overwrite conflict | a message box defaulting to Yes | — | Return. Better: script the demo so no conflict can happen |

A prompt selects its prefilled text only on its **second** paint, so wait
≥1.6 s after opening one before typing into it.

### Traps that cost a recording

- **A pane does not re-list itself** after a command creates a file in it. Press
  `Ctrl+R` (reload) before filtering for something the demo just made — this is
  why chapter 7 reloads after packing and chapter 3 reloads after copying.
  Without it the filter matches nothing, the cursor stays where it was, and
  every following step acts on the wrong file.
- **`Return` on a `.jpg`/`.mp4` in the file list launches the Windows default
  application** over your recording. Only press it on a directory, on a `.zip`
  (which fman rewrites into "open directory"), or inside a dialog.
- **Escape does not close the text viewer in edit mode** — use the viewer
  palette's `exit`.
- **Typing goes to whatever has focus.** If a prompt or progress dialog is still
  up, the rest of the script types into it and silently does nothing.

Pace for viewers: ~0.6–1.2 s after each result, longer after a copy or a video
start, and end with a `Pause(1.0)` so the recording doesn't cut off abruptly.

## Add a new demo

1. Add a `DemoScript` to `DEMOS` in
   `src/main/python/fman/impl/demo_scripts.py` with a new `id` and `name`.
   Verify chords against
   `src/main/resources/base/Plugins/Core/Key Bindings (Windows).json` and
   palette queries as described above.
2. Add a matching entry to the `demos` array in `tools/create_media/fman.json`
   (`id`, `name`, `fps`, `width`, `height`, `formats`). Ids ≥ 3 automatically
   get the scratch fixture folders. A stills-only demo like `themes` sets
   `"formats": []` and needs no `CAPTIONS` entry.
3. If the name starts with `tour-`, add a caption for it in `CAPTIONS` in
   `tools/create_media/build_tour.py` — the build refuses to run otherwise.
4. Preview it, check its side effects, then record:
   `tools\demos_record.bat --demo <id>`.

## Troubleshooting

| symptom | cause | fix |
|---------|-------|-----|
| `ModuleNotFoundError: fbs_runtime` | wrong interpreter — the deps are in one interpreter's user site-packages | set `FMAN_PYTHON` to that `python.exe` |
| the demo runs but nothing after step N takes effect | a dialog still had focus, or a prompt was typed into before it selected its prefill | longer `Pause` before typing; check the dialog table above |
| a filter finds nothing right after the demo created a file | the pane hasn't re-listed | `PressKey('Ctrl+R')` before filtering |
| a photo viewer or media player opens mid-recording | `Return` was pressed on a file the cursor happened to be on | fix the cursor position; never press Return on a non-directory, non-`.zip` |
| the palette runs the wrong command | a shorter command title matched the query first | lengthen the query; see the table above |
| a clock/monitor overlay is visible in every frame | an always-on-top desktop widget | close it and re-record; the capture is a screen region |
| a video demo records a download dialog | libmpv isn't cached in the demo profile | copy `libmpv-2.dll` into `%TEMP%\fman-demo-profile\Local\libmpv\` |
| `Demo exceeded 300s cap` | one script is too long | split it into chapters |
| `No demo event for 60s` | a long stretch with no `Screenshot` step | add `Screenshot` heartbeats or shorten the chapter |
| the recording is huge or the machine swaps | frames are all held in RAM | shorter chapters, or a lower `fps` in `fman.json` |
| `demo_build_tour.bat` says a clip is missing | that chapter wasn't recorded | record it; the message names the exact command |
| a theme is missing from the themes GIF | its still was never written — the typed name matched another theme first | lengthen or rename; see [The themes demo](#the-themes-demo) |
| a still shows the wrong theme | same cause, but the file name says otherwise | as above; the file count alone won't catch it |

Full step reference: the connector repo's `docs/WRITING_DEMOS.md`; full
app-side contract: the tool repo's `docs/AUTOMATION_INTERFACE.md`.
