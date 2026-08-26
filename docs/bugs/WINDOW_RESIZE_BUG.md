# Window shrinks on restart when the title bar is off (unconfirmed)

**Status:** not reproduced. Research parked — reopen if it happens again.

**Report:** with `toggle_title_bar` off, reopening fman restores the saved
window dimensions "without taking the bar into consideration", so the window
comes back smaller than it was.

Related: [`docs/WINDOW_TITLE_AND_BARS.md`](../WINDOW_TITLE_AND_BARS.md),
[`docs/functions/window-bars.md`](../functions/window-bars.md).

## What was measured

Machine: Windows 11, single 3840x2160 screen, PyQt5 5.15.2, `python build.py run`.
Window rects read with `GetWindowRect` / `GetClientRect` /
`DwmGetWindowAttribute(DWMWA_EXTENDED_FRAME_BOUNDS)`; the saved geometry decoded
straight out of `%APPDATA%/fman/Local/Session.json` (`window_geometry`, a Qt
`saveGeometry` blob — see `SessionManager.on_close`).

### 1. Save/restore round-trips exactly

Three full close/relaunch cycles, geometry identical every time:

| case | saved in `Session.json` | measured after relaunch |
|---|---|---|
| frameless, normal | frame/normal/geom all `1915x1079 @1916,16` | `1915x1079` |
| frameless, maximized | `max=1`, frame `3840x2160` | `3840x2160` |

So `saveGeometry`/`restoreGeometry` lose nothing, in either window state.

### 2. Two theories tested and killed

- **Qt clamps the restored size.** Qt 5.15's `restoreGeometry` has a
  "don't restore a lost window" path that clamps to
  `availableGeometry() - 20`. Fed it a hand-built blob at exactly screen size:
  restored unclamped. Not it.
- **`restoreGeometry` subtracts the frame.** It sets `normalGeometry`, i.e. the
  client rect, and the app is already frameless when it runs
  (`WindowChrome.apply` runs before `show()`), so there is no frame to subtract.

### 3. The toggle keeps the outer rect, not the visible one

Same window, one `toggle_title_bar` apart:

```
bar OFF: win 1915x1079  client 1915x1079  DWM-visible 1915x1079 @1916,16
bar ON : win 1915x1079  client 1899x1040  DWM-visible 1901x1072 @1923,16
```

`GetWindowRect` includes Windows 11's ~8 px invisible resize border; the DWM
extended frame bounds do not. `MainWindow.set_title_bar_visible` compensates via
`frameGeometry()`, which counts that invisible border — so the *visible* window
changes by 14x7 px across a toggle even though the outer rect is preserved.
Small, but it is a real asymmetry and it is in the direction of "smaller with the
bar on", not "smaller with it off".

### 4. The compensation is needed in one direction, unverifiable in the other

Isolated PyQt5 harness, toggling the flag with and without the
`setGeometry(frameGeometry())` compensation:

| direction | with compensation | without |
|---|---|---|
| framed -> frameless | `902x632` kept | shrinks to `900x600` |
| frameless -> framed | inconclusive (see below) | inconclusive |

### 5. FancyZones contaminates every framed-window measurement

PowerToys FancyZones is running on this machine (`PowerToys.FancyZones`). It
snaps **framed** windows into a zone and ignores **frameless** ones (WS_POPUP).
In the harness, every window that gained a title bar was teleported to
`1901x1072 @1923,16` — the top-right zone — regardless of the size it had been
given. That makes the frameless -> framed row above meaningless here, and it
means the real fman window's apparent "outer rect preserved when turning the bar
back on" may have been FancyZones, not fman's own code.

This is also a plausible source of the original report: with the bar **on**,
FancyZones re-sizes fman into its zone on every launch, so whatever fman restored
is overwritten and always looks right. With the bar **off** fman is left alone,
so its own restored geometry is what you see — and any difference from the
zone-sized previous session reads as "the window came back wrong".

## The one defect actually found in the code

`MainWindow._framed_geometry` (`src/main/python/fman/impl/widgets.py:346`, used
at `:508`) is in-memory only:

1. Bar on, window client `C`. Toggle off -> client grows to the old outer rect,
   `_framed_geometry = C`.
2. Close, restart. Bar off is restored from `Settings.json`, but
   `_framed_geometry` is `None` again — it is never persisted.
3. Toggle the bar back on -> `self._framed_geometry or geometry` falls through to
   the current (grown) client rect, so the window has no memory of the size it
   is supposed to return to.

Fix, if this is ever worth doing: persist it next to `window_geometry` in
`Session.json`. `SessionManager.on_close` already writes the window's geometry;
a `get_framed_geometry()` on `MainWindow` can derive the value without extra
bookkeeping — while the bar is visible it is just `self.geometry()`, and only the
bar-hidden case needs the remembered rect.

Not done, because the symptom it would fix could not be observed on this machine
(FancyZones preserves the outer rect on its own), and the fallback is only
reachable for one toggle after a restart.

## Strongest lead: the bar state and the geometry are saved by different code

`WindowChrome._save` writes `title_bar_visible` to `Settings.json` at toggle
time; `SessionManager.on_close` writes `window_geometry` to `Session.json` at
close time. Nothing keeps the two in agreement, and the geometry compensation in
`set_title_bar_visible` only runs during a toggle.

After the test runs above, the two files were left disagreeing:

```
Settings.json  title_bar_visible: False        (bar off)
Session.json   normal/geom:  1899x1040         (a FRAMED client rect)
               frame:        1915x1079
```

The next launch applies "bar off" before `show()` and then restores a *client*
rect that was measured with a frame — a frameless window of 1899x1040 where the
previous one covered 1915x1079. Smaller by exactly the frame, 16x39 px. That is
the reported symptom.

How the pair gets out of sync is the open question. Candidates, none confirmed:

- The app exits without a clean `closeEvent` (crash, kill), so the bar setting is
  already `False` on disk from the toggle while the geometry on disk is still the
  framed one from an earlier clean close.
- `set_title_bar_visible` is `@run_in_main_thread`; if the toggle's `setGeometry`
  has not been applied by the time `on_close` runs, `saveGeometry` captures the
  uncompensated rect while `WindowChrome` has already flushed the new setting.

Either way the fix is the same shape: make the saved geometry self-describing
rather than depending on the bar state that happened to be live when it was
written — e.g. always save the framed geometry (see `_framed_geometry` above) and
let `set_title_bar_visible` grow it at startup, so restoring never needs to know
which state the rect was captured in.

## If it comes back, get these first

- Is the whole window smaller, or only the pane area?
- Bar off from app start, or toggled off during that session?
- Once, or cumulative on every restart?
- Is FancyZones (or any window manager) managing the window?
- `Session.json` `window_geometry` decoded before and after the restart — that
  splits "fman saved the wrong thing" from "something resized it afterwards".
