# Set window opacity

Makes fman's window see-through, from the
[command palette](../COMMAND_PALLETTE.md). Applied immediately, remembered
across restarts.

## Usage

1. Press **`Ctrl+Shift+P`** and run **"Set window opacity"**.
2. A quicksearch list offers **Theme default**, then `100%` down to `70%` in
   5% steps. The value in use is preselected and marked `current`.
3. Pick one (Enter, or click). The window fades right away.

**Theme default** drops your choice again, so the active theme decides — see
[Themes](../THEMES.md#opacity). That is the way back, not "100%": picking
`100%` pins the window opaque under *every* theme, including one that ships
translucent.

## Commands

| Command name          | Palette label      | Default key binding |
|------------------------|---------------------|----------------------|
| `set_window_opacity`   | Set window opacity  | none (palette only)  |

*Transparency*, *opacity*, *alpha* and *translucent* find it too — they are
hidden keywords, so the row still reads "Set window opacity". See
[the command palette](../COMMAND_PALLETTE.md#hidden-search-keywords).

Bind it to a key in `Key Bindings.json` like any other command
(see [`docs/KEYBINDINGS.md`](../KEYBINDINGS.md)):

```json
{ "keys": ["Ctrl+Alt+O"], "command": "set_window_opacity" }
```

## Notes

- **The whole window fades, text included.** fman does not do
  background-only translucency — that would need a translucent widget
  background plus per-platform blur, and it breaks the file list's painting.
- **Only the main window fades.** Dialogs (command palette, prompts, alerts,
  progress) are separate top-level windows and stay fully opaque, so the
  thing you are reading or typing into never gets harder to read than the
  file list behind it.
- The range is **0.3 to 1.0**. The picker stops at 70% because below that
  the file list gets hard to read against whatever is behind it; the
  `set_window_opacity` API goes to 0.3 if you bind your own command.
- **Your setting beats the theme's.** Once you pick a value it survives
  every theme switch, including to a theme that asks for its own opacity
  (like **Matrix**). **Theme default** hands control back.
- **Windows: another tool can silently undo it.** The opacity lives in the
  window's `WS_EX_LAYERED` extended style. A window manager that *overwrites*
  the extended style instead of OR-ing into it —
  `SetWindowLong(hwnd, GWL_EXSTYLE, 0)`, a common line in AutoHotkey
  maximize/resize scripts — drops that bit and the window turns opaque again.
  fman does not notice, so it still reports the old value; re-pick it from
  the palette to bring the fade back, or fix the script.
- A file viewer that is already open fades with the window — it is a child
  widget, not a separate window, unlike the color case described in
  [Select theme](select-theme.md).

## Where it lives

- Command: `Plugins/Core/core/commands/theme.py` (`SetWindowOpacity`)
- Resolution and live application: `fman/impl/themes.py` (`ThemeController`)
- Public API: `fman.get_window_opacity()` / `fman.set_window_opacity(value)`
  (`value=None` clears the override)
- Saved as `window_opacity` in `%APPDATA%/fman/Local/Settings.json`, beside
  `theme` — the same file the palette is built from before any plugin loads
