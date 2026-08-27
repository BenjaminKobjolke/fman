# Recording plugin demos

fman's demo machinery can film a **third-party plugin**, not just fman itself.
The result is one GIF published in two places: the plugin's row in the
[README's plugin list](../README.md#plugins), and the plugin's own README in
its own repository.

This page covers only what is specific to plugin clips. Everything shared — the
install, the step vocabulary, the recorder's RAM and timeout limits, the pane
sort order, the palette-query traps — is in [DEMOS.md](DEMOS.md), and you need
to have read that first.

One command records everything on this page:

    tools\demo_plugins_record.bat

## Why a category of its own

There are three demo prefixes and they are not interchangeable:

| prefix | what it films | published as |
|--------|---------------|--------------|
| `tour-*` | fman's own feature tour | `media/demos/tour/feature-tour.mp4` |
| `feature-*` | one fman feature, standalone | `media/demos/features/*.gif` |
| `plugin-*` | a third-party plugin | `media/demos/plugins/*.gif` |

`build_tour.py::chapters()` joins **every** `tour-*` demo, so naming a plugin
clip `tour-f-*` silently lengthens the README's hero video. That much is true of
`feature-*` too. What makes `plugin-*` a separate category rather than a third
`feature-*` clip is that these film **software this repository does not ship**:

- They carry a prerequisite no other demo has — the plugin must be installed on
  the recording machine (see [The seeding contract](#the-seeding-contract)).
- They raise a question no other demo raises: *whose* copy of the plugin got
  recorded. The launcher copies your working checkout verbatim, uncommitted
  edits included.
- They are encoded differently, because plugin UI is often animated where fman's
  own is mostly static (see [Encoding](#encoding)).

## The seeding contract

`run_fman_demo.bat` wipes `%TEMP%\fman-demo-profile\Plugins` on **every** run,
before any per-id setup. That wipe is the whole reason recordings are
reproducible: a recordist's third-party plugins prepend their key bindings (so
they beat Core's) and add palette commands that change what a typed query
resolves to. Everything a demo needs is then written back into the fresh tree.

For id 10 that is:

| what | from | into |
|------|------|------|
| the plugin under test | `%APPDATA%\fman\Plugins\User\MatrixRain` | `Plugins\User\MatrixRain` |
| the demo font CSS | `tools/create_media/demo_Theme.css` | `Plugins\User\DemoFont\Theme.css` |
| right-pane fixtures | `examples/right_pane` | the run's scratch `RIGHT` folder |

**Seed the plugin under test and nothing else.** Copying all of
`%APPDATA%\fman\Plugins` would put your key bindings and palette commands back
into the take — exactly what the wipe exists to prevent — and the take would
look fine while quietly filming a different program than the one a viewer will
install. MatrixRain is safe to seed for the opposite reason: its
`Key Bindings.json` is `[]` by design, so it steals no chord from Core.

Plugin load order is shipped → `Third-party\` → `User\`, with `User\Settings`
forced last (`fman/impl/plugins/discover.py`). Seeding under `User\` therefore
reproduces what a user who copied the plugin in by hand would get.

**A missing plugin aborts the run.** This is deliberately *not* a warning like
the missing-libmpv one: an absent libmpv degrades a take you can still judge by
eye, whereas an absent plugin produces a perfectly clean recording of fman
*without* the plugin, in which every palette query matches nothing and the panes
simply never change. The launcher exits 1 with:

    ERROR: MatrixRain is not installed in %APPDATA%\fman\Plugins\User - cannot record demo 10.

## The MatrixRain clip

`plugin-matrix-rain` (id 10) shows the rain in **one pane**, then in **both**.

| step | what is on screen |
|------|-------------------|
| palette → `matrix rain in other pane` | the right pane rains; the left is still a file list |
| palette → `matrix rain transparency` → `70` | the right pane's rain goes translucent, its file list showing through |
| palette → `matrix rain` | the left pane rains too — both panes, both translucent |
| `Escape`, `Tab`, `Escape` | back to two file lists |

Two things about that order are not stylistic.

**The other-pane command comes first on purpose.** MatrixRain has no "both
panes" command — only *Matrix rain* (this pane, takes focus) and *Matrix rain in
other pane* (the other pane, focus stays put). Running the other-pane one first
is what produces one-pane-then-both at all. It also keeps the keyboard in the
left **file list** for every palette step: `MatrixRainView.keyPressEvent`
swallows Escape/Return/Backspace/Tab and only forwards the rest, so whether
`Ctrl+Shift+P` reaches Core's palette from inside a mounted rain widget is
untested. This ordering never has to find out.

**Every query is an exact alias.** `match_titles_or_keywords`
(`core/quicksearch_matchers.py`) returns bucket 0 for a query that *equals* a
lowercased alias, ahead of every fuzzy tier — so `matrix rain`,
`matrix rain in other pane` and `matrix rain transparency` each resolve to
exactly one command, with no shortest-title tie-break involved. That is a
stronger guarantee than the `view file` / `comp dir` queries in
[DEMOS.md](DEMOS.md) get, and it is worth preserving here specifically: a
plugin's command titles are outside this repository's control, so a query that
relies on ranking can be broken by an edit in someone else's repo.

The clip is **34.1 s scripted**, about 35.6 s of wall clock once the player's
500 ms start delay and 1 s end hold are counted. That is inside `DEMO_CAP_S`
(300 s) and under `EVENT_TIMEOUT_S` (60 s) on `demo_started` alone, so it needs
no `Screenshot` heartbeats.

Its settings are deterministic without any seeding: the plugin persists through
Core into `Plugins\User\Settings\Matrix Rain (Windows).json`, which is inside
the wiped tree, so every run starts at the plugin's own defaults
(`transparency: 0`, `fps: 20`, `columns: 0`) and the transparency prompt always
opens on the same value.

## Encoding

`tools/demo_build_plugin_gifs.bat` uses the same two-pass
`palettegen`/`paletteuse` subroutine as the feature GIFs, then hands the result
to `gifsicle`. Every setting differs, and each one was measured on the
MatrixRain clip rather than guessed:

| knob | feature GIFs | plugin GIFs |
|------|--------------|-------------|
| width | 800 | **360** |
| fps | 5 | **4** |
| `max_colors` | 64 | **32** |
| dither | `bayer` | **`none`** |
| post-pass | — | **`gifsicle -O3 --lossy=60`** |

Matrix rain is close to the worst case for GIF: every pixel changes every frame,
so inter-frame delta compression buys nothing and each frame is stored whole. At
the feature clips' settings the same 34 s take came out at **7.1 MB**.

**What did not help**, all measured on that take:

| change | result |
|--------|--------|
| 64 → 24 colours | 7.1 → 6.6 MB |
| dithering off | no change |
| `paletteuse=diff_mode=rectangle` | no change |
| `palettegen=stats_mode=diff` | no change |

The last two are the ones worth knowing about, because they *sound* like the
right tool: both exploit regions that stay still between frames, and this clip
has none. Only two levers move the number at all.

**Pixel count.** The dominant term. It is also where the original 640 px was
simply wasteful: the README renders this GIF at 360, so encoding at 640 paid
four times the pixels to throw them away.

Whether you can afford a small width depends on what the clip demonstrates.
The `feature-*` clips show *reading and typing* — a fuzzy query being matched, a
log being followed — so their text has to stay legible, which is what the 800 px
and the [demo font CSS](DEMOS.md) are for. This one demonstrates an **effect**;
nobody needs to read the file names to see rain fill one pane and then both. A
plugin clip that does hinge on text needs a wider setting and a bigger budget.

**`gifsicle --lossy`.** Worth about 40%. It lets nearly-identical pixels share a
palette entry — exactly the redundancy a rain of glyphs has, and exactly what
ffmpeg's palette stage cannot exploit. It is optional: without gifsicle on
`PATH` the build prints a note and ships the larger file.

Together those two put the shipped GIF at **1.4 MB** for the full 34 s clip.

Budget: **~1.5 MB**. If a clip overshoots, in order:

1. lower `GIF_WIDTH` — by far the biggest lever
2. raise `GIF_LOSSY` (100 is the practical ceiling before banding shows)
3. lower `GIF_FPS`, accepting that the motion gets choppier
4. shorten the holds in the script and re-record

All four are variables at the top of the build bat, except the last.

## Calibrate the capture fps

The likeliest way a plugin clip ships wrong. The recorder writes the frames it
actually captured at whatever fps the config names, so a config fps *above* the
real capture rate makes the clip play fast and misrepresent how fast the
software is. [DEMOS.md](DEMOS.md) already records this happening at ~4.8 fps
with an animated theme merely sitting *behind* the window.

A plugin that animates two whole panes is heavier than anything else recorded
here, so treat this as a required step, not a check:

1. Record once at the configured `fps` (5 for id 10).
2. Divide the frame count the tool prints by the clip's wall-clock seconds
   (35.6 for id 10).
3. If the result is meaningfully lower, put that value in `fman.json` **and** in
   `GIF_FPS` in `demo_build_plugin_gifs.bat`, then re-record.

## Publishing

The same GIF goes to two repositories:

- **fman** — `media/demos/plugins/<name>.gif` is committed; the recorded
  `media/demos/plugin-*/demo.mp4` is a gitignored intermediate. The README's
  plugin table shows it with inline HTML (`<img width="360">`, its native size),
  because Markdown
  image syntax cannot constrain width inside a table cell.
- **The plugin's own repo** — `demo_build_plugin_gifs.bat` copies the finished
  file into the installed checkout's `media/` folder, since that checkout *is*
  the plugin's repository. **Committing and pushing it there is yours to do** —
  this repo has no business writing history in another one.

## Add another plugin demo

1. Install the plugin under `%APPDATA%\fman\Plugins\User\`, and commit whatever
   you want filmed — the launcher copies your working tree verbatim.
2. Add a `DemoScript` to `PLUGIN_CLIPS` in
   `src/main/python/fman/impl/demo_scripts.py` with a new id and a `plugin-*`
   name. Prefer palette queries that **equal** an alias exactly, and verify
   chords against the plugin's `Key Bindings.json` as well as Core's.
3. Add the matching entry to `demos` in `tools/create_media/fman.json`
   (`fps: 5` to start, `formats: ["mp4"]`, 1280x800).
4. In `tools/create_media/run_fman_demo.bat`: add the id to the `FONT_CSS`
   lines, and add a seeding block that copies **only that plugin** and exits 1
   if it is absent.
5. Add a `call :gif <demo-name> <gif-name>` line to
   `tools/demo_build_plugin_gifs.bat` and a `--demo <id>` line to
   `tools/demo_plugins_record.bat`.
6. Record, calibrate the fps, check the GIF size.
7. Publish both copies: the `Demo` cell in this repo's README plugin table, and
   the plugin's own README.

If `demo_scripts.py` passes 300 lines, split `PLUGIN_CLIPS` into
`demo_scripts_plugins.py` and `DEMOS.update()` it in — the same move
`demo_scripts_tour.py` already makes for the tour chapters.

## Troubleshooting

Start with [DEMOS.md](DEMOS.md); these rows are specific to plugin clips.

| symptom | cause | fix |
|---------|-------|-----|
| `ERROR: MatrixRain is not installed...` and no recording | the plugin is not in `%APPDATA%\fman\Plugins\User` | install it there; this is a hard stop by design |
| the take is clean but nothing ever happens on screen | the plugin was not loaded, so every palette query matched nothing | check `%TEMP%\fman-demo-profile\Plugins\User\<Plugin>\` exists after the run; record via `tools\demo_plugins_record.bat` |
| a palette query opens the wrong thing | the plugin renamed a command, or a Core command title now matches better | re-check the alias; prefer a query that equals an alias exactly |
| the GIF is several megabytes | full-frame animation defeats GIF delta compression | walk the ladder under [Encoding](#encoding) |
| the clip plays faster than the software runs | capture could not hit the configured fps | recalibrate; see [Calibrate the capture fps](#calibrate-the-capture-fps) |
| the plugin's README shows an old clip | the copy step only runs when the checkout exists, and never commits | re-run the build, then commit in the plugin's repo |
