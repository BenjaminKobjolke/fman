# File viewers

fman can show a file's contents **inside the active pane**, replacing the
file list until you close it — no external app launch, no waiting. This lets
you peek at (and, for text, quickly edit) a file without leaving fman.

## Opening a viewer

Put the cursor on a file and run **"View file"** from the
[command palette](../COMMAND_PALLETTE.md) (`view_file`), or
**"View file in other pane"** (`view_file_in_other_pane`) to open it in the
opposite pane and keep browsing. Neither has a default key binding — bind your
own if you want one. See
[`docs/functions/view-file.md`](../functions/view-file.md).

**"View file" picks the viewer by file type** — you don't choose:

| File type | Viewer | Recognized by |
|-----------|--------|----------------|
| Text-like (anything not image/video/binary) | [Text viewer](../views/TEXT_VIEWER.md) | fallback; binaries (NUL byte) alert instead |
| Images | [Image viewer](../views/IMAGE_VIEWER.md) | `.png .jpg .jpeg .gif .bmp .webp .ico .svg` |
| Video | [Video viewer](../views/VIDEO_VIEWER.md) | `.mp4 .m4v .mkv .webm .avi .mov .wmv .flv .mpg .mpeg .ogv .3gp .ts` |

## The three viewers at a glance

| | [Text](../views/TEXT_VIEWER.md) | [Image](../views/IMAGE_VIEWER.md) | [Video](../views/VIDEO_VIEWER.md) |
|-|------|-------|-------|
| Editable | Yes (UTF-8, untruncated) | No | No |
| Zoom | Font size | Scale + pan | — (fills pane) |
| Extras | auto-reload / tail mode | animated GIFs play | play/pause, seek, volume (persists) |
| Backend | `QPlainTextEdit` | `QPixmap` / `QMovie` | [python-mpv / libmpv](../views/VIDEO_VIEWER.md#playback-backend) |

## Shared behaviour

All three viewers work the same way where it counts:

- **Close:** `Escape` / `Enter` / `Backspace` returns to the file list, cursor
  back on the same file. (Text edit mode with unsaved changes prompts first.)
- **Switch panes:** `Tab` / `Shift+Tab`, same as the file list. The viewer
  stays open; `Tab` back returns focus to it. (Text: view mode only — in edit
  mode `Tab` types a tab.)
- **Own command palette:** `Ctrl+Shift+P` opens a **viewer-scoped** palette,
  separate from the global one (which can't reach a viewer while the file list
  is hidden) — see [`docs/COMMAND_PALLETTE.md`](../COMMAND_PALLETTE.md).
- **Next / previous file:** **"Next file"** / **"Previous file"** in the viewer
  palette advance to the neighbouring file in the directory (following the
  pane's own sort order) without closing the viewer. A per-viewer
  **"Advance only for same type"** toggle (on by default) keeps e.g. the image
  viewer from stepping into a video; turn it off to walk across every viewable
  file, switching viewer type as needed. No default keys — bind your own (see
  [`docs/KEYBINDINGS.md`](../KEYBINDINGS.md#viewer-specific-bindings) for
  suggestions).
- **Bindable keys:** viewer actions are pseudo-commands you rebind in a
  **separate** `Viewer Key Bindings (<OS>).json` — see
  [`docs/KEYBINDINGS.md`](../KEYBINDINGS.md#viewer-specific-bindings).
- **Per-pane, one at a time:** opening a viewer replaces whatever viewer is
  already open in that pane; the other pane is unaffected.
- **Theme-aware:** background/letterbox colors follow the active file-list
  palette, not a hardcoded value — see [`docs/THEMES.md`](../THEMES.md).

For per-viewer detail (usage, zoom, controls, limits, implementation) see each
viewer's own doc linked above.
