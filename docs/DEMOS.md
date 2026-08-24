# Recording demos

fman can record animated demos (GIF/MP4 + PNG stills) of its UI with the
[automated-application-screenshots](https://github.com/BenjaminKobjolke/automated-application-screenshots)
tool. The recorded `overview` demo is shown in the [README](../README.md#demo).

## How it works

In demo mode fman plays a scripted sequence of UI actions and reports events
over a socket so the tool can capture the window. The wiring:

- `src/main/python/fman/impl/demo.py` — the PyQt5 demo player and the `DEMOS`
  registry (one `DemoScript` per recordable demo).
- `src/main/python/fman/impl/application_context.py` — `run()` enters demo mode
  when `--automation-demo` is on the command line (`_run_demo()`), and skips the
  splash/tutorial and single-instance handoff so the recording is clean.
- `tools/create_media/fman.json` — the tool-side config (window size, formats,
  output folder).
- `tools/create_media/run_fman_demo.bat` — launcher the tool starts per run.
- `tools/demos_record.bat` — one command that drives the whole recording.

The two panes are populated from `examples/left_pane` (images + a video) and
`examples/right_pane` (text/markdown), passed as trailing paths on the command
line, so every recording starts from the same deterministic state.

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

## Record

    tools\demos_record.bat            REM every demo
    tools\demos_record.bat --demo 1   REM one demo (any tool args pass through)

Output lands in the tool's configured folder — currently
`media/demos/<name>/` (see `output_dir` in `tools/create_media/fman.json`):
`demo.gif`, `demo.mp4`, and one PNG per `Screenshot` step.

If `python` on your machine isn't the interpreter that has fman's deps, set
`FMAN_PYTHON` to the right `python.exe` before recording. (The launcher drops
the tool's `uv` virtualenv from `PATH` so plain `python` resolves to fman's
base install.)

## Preview a demo without the tool

Fastest way to iterate on pacing — plays visually, reports nothing, quits itself:

    set PYTHONPATH=src\main\python
    python src\main\python\fman\main.py --automation-demo 1 examples\left_pane examples\right_pane

## Add a new demo

1. Add a `DemoScript` to `DEMOS` in `src/main/python/fman/impl/demo.py` with a
   new `id` and `name`, built from the step types `Pause`, `TypeText`,
   `PressKey`, `Screenshot` (and `Command`). Keys must be portable Qt chords
   (e.g. `"Ctrl+Shift+P"`, `"Down"`, `"Escape"`) — verify commands against
   `src/main/resources/base/Plugins/Core/Key Bindings (Windows).json`.
2. Add a matching entry to the `demos` array in `tools/create_media/fman.json`
   (`id`, `name`, `width`, `height`, `formats`).
3. Record it: `tools\demos_record.bat --demo <id>`.

Pace for viewers: ~0.6–1.2 s pauses after each result, and end with a
`Pause(1.0)` so the recording doesn't cut off abruptly. Full step reference:
the connector repo's `docs/WRITING_DEMOS.md`; full app-side contract:
the tool repo's `docs/AUTOMATION_INTERFACE.md`.
