# Check for updates

fman checks the latest published GitHub release five minutes after its main
window appears, then every 24 hours while it remains open. The automatic check
does not run in demo mode. It stays quiet when the app is current or the check
fails. When a newer release exists, a dialog names both versions and offers to
open its download page. Each release is announced automatically only once.

You can check at any time from the command palette (`Ctrl+Shift+P`). The manual
command always reports the result, including an up-to-date or failed check, and
offers the download page even if it has announced that release before.

## Commands

| Command name | Palette label | Keywords | Default key binding |
| --- | --- | --- | --- |
| `check_for_updates` | Check for updates | update, upgrade, new version, latest release, github | none |

The installed release label comes from the newest bundled `release_notes/`
folder. When there are no bundled notes, it uses the application version with
build `0`. GitHub's latest published release tag must use the same
`<version>_<build>` form.

An internal build with no new release notes may read as the previous public
release. A source checkout reads as the newest authored release notes. Neither
case identifies a distinct internal build. A stalled GitHub connection can keep
one daemon worker occupied; the UI remains responsive.
