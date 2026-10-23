# Upstream issues ledger

Which open issues of the original fman tracker have been looked at, and what was done.
Maintained by the `upstream-issues` skill (`.claude/skills/upstream-issues/SKILL.md`).

Source: https://github.com/mherrmann/fman/issues (read-only — never comment there)

An issue that is in this table has been handled. The next run takes the next five open
issues that are not in it, oldest first. Newest rows go at the top.

Status: `fixed`, `already fixed` (works here already), `skipped` (with reason),
`deferred` (fixable, but too big or needs a decision — with what is needed).

| Issue | Title | Labels | Status | Date | Note |
|-------|-------|--------|--------|------|------|
| [#17](https://github.com/mherrmann/fman/issues/17) | Icons are sometimes not displayed | bug, windows | deferred | 2026-10-23 | The report gives no reproducible steps or affected file types; needs a concrete Windows example before a fix can be pinned. |
| [#16](https://github.com/mherrmann/fman/issues/16) | Files and directories in SMB-Shares are not displayed | bug, windows | already fixed | 2026-10-23 | UNC paths use `LocalFileSystem.iterdir` and `os.listdir`; the Windows Network view enumerates servers and shares. |
| [#15](https://github.com/mherrmann/fman/issues/15) | Icon for .lnk files on Desktop are not shown | bug, windows | already fixed | 2026-10-23 | Windows shell icons are used by the System set; when another set is active, the executable-icon toggle restores real `.lnk` icons. |
| [#13](https://github.com/mherrmann/fman/issues/13) | .lnk to virtual network drive (Z:) is not displayed | bug, windows | deferred | 2026-10-23 | The issue has no description or reproduction details; needs a concrete shortcut and drive setup to verify. |
| [#12](https://github.com/mherrmann/fman/issues/12) | .lnk files are displayed as the name of the link target instead of the link itself | bug, windows, 1 vote | already fixed | 2026-10-23 | The Name column uses the filesystem name, which returns the final local path component without resolving the `.lnk` target. |
| [#1](https://github.com/mherrmann/fman/issues/1) | Icons have a low resolution | bug, mac, 5 votes | skipped | 2026-10-23 | macOS/Linux Finder `.icns` issue; Windows icons come from the shell or crisp vector icons. |
| [#3](https://github.com/mherrmann/fman/issues/3) | Trying to delete un-deletable file raises exception | bug, linux, 2 votes | already fixed | 2026-10-23 | Core deletion reports access errors and offers UAC elevation for protected files. |
| [#5](https://github.com/mherrmann/fman/issues/5) | Try deleting un-deletable file: fman freezes | bug, mac | skipped | 2026-10-23 | macOS-only report; deletion runs as a background task here. |
| [#8](https://github.com/mherrmann/fman/issues/8) | Can't resize fman to width < status bar | bug | fixed | 2026-10-23 | `widgets.py` MainWindow status bar label; `status_bar_test.py`. |
| [#9](https://github.com/mherrmann/fman/issues/9) | Can't enter "^" and "~" with a Swedish keyboard layout | bug, linux, 2 votes | skipped | 2026-10-23 | Linux-only keyboard-layout report; upstream comments confirm it works on Windows. |
