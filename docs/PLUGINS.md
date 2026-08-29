# Plugins

fman is plugins all the way down — the file list, the archive support and
every command in the palette live in the shipped **Core** plugin, loaded
through the same mechanism your own plugins use.

This page is about *running* plugins: installing them, reloading them without
restarting, and what fman tells you when two of them collide. For writing one,
see [`docs/PLUGINS_API.md`](PLUGINS_API.md). For what *Install plugin*
does and which GitHub endpoints it uses, see
[`docs/INSTALL_PLUGINS.md`](INSTALL_PLUGINS.md).

## Where they live

| Directory | What goes there |
|-----------|-----------------|
| `<resources>/Plugins` | The shipped **Core** plugin. Loads first, and is never reloaded at runtime. |
| `%APPDATA%\fman\Plugins\Third-party` | Plugins installed with *Install plugin*. |
| `%APPDATA%\fman\Plugins\User` | Your own. `User\Settings` always loads **last**, so its JSON wins. |

On macOS and Linux, `%APPDATA%\fman` is
`~/Library/Application Support/fman` and `~/.config/fman`.

Load order is shipped → third-party → user. A plugin is a directory containing
a Python **package** (a subdirectory with `__init__.py`) — see
[Plugin layout](PLUGINS_API.md#plugin-layout).

## The commands

All four are in the [command palette](COMMAND_PALLETTE.md) (`Ctrl+Shift+P`),
none has a default key binding:

| Command | Does |
|---------|------|
| **Install plugin** | Lists GitHub repos tagged `fman` + `plugin`, downloads the latest release (or the latest commit if there is none) into `Plugins\Third-party\`, and loads it immediately. See [`docs/INSTALL_PLUGINS.md`](INSTALL_PLUGINS.md). |
| **List plugins** | Fuzzy-search every installed plugin; picking one opens its directory in the pane. Third-party entries show the installed release tag or commit. |
| **Remove plugin** | Unloads a third-party plugin and deletes its directory. Only third-party ones are offered — plugins under `User\` are yours to delete by hand. |
| **Reload plugins** | Unloads and reloads every third-party and user plugin, in place. |

## Reload plugins

*Reload plugins* is the edit-test loop: change a plugin's `.py` file, run it,
see the change — no restart.

What it does and does not cover:

- It unloads in reverse load order, then loads again in load order. Every
  registration a plugin made — commands, listeners, file systems, columns,
  viewers, fonts, CSS, key bindings, context menus — is undone by the inverse
  action recorded when it was made, so nothing leaks.
- Pane locations are preserved across the reload. A pane sitting inside a
  file system that gets reloaded would otherwise lose its path.
- **Core is not reloaded.** Only `Third-party\` and `User\`. To pick up a
  change in Core, restart fman.
- **fman itself is not reloaded.** Anything under `fman.impl` — the plugin
  loader included — is only re-read on restart. When you are working on fman's
  own source, *Reload plugins* runs the version that was loaded at startup.

## Two plugins, one package name

Python package names are **global**: they are keys in `sys.modules`, shared by
every plugin in the process. Two plugins whose package directories have the
same name are therefore the same module as far as Python is concerned, and
only one of them can win — the one that loads last.

This is easy to hit without noticing, because a plugin's *directory* name and
its *package* name are two different things:

```
%APPDATA%\fman\Plugins\Third-party\SyncSelectedFilesToOtherPaneForWindows\
    sync_selected_files_to_other_pane_for_windows\__init__.py

%APPDATA%\fman\Plugins\User\FManSyncSelectedFilesToOtherPaneForWindows\
    sync_selected_files_to_other_pane_for_windows\__init__.py     <- same package
```

Two differently-named plugin folders, one package name. Typically the same
plugin installed twice: once from the plugin list, once as a git clone you
edit.

fman says so on load, rather than letting you wonder why your edits do
nothing:

```
Two plugins contain a package named 'sync_selected_files_to_other_pane_for_windows':

C:\...\Plugins\Third-party\SyncSelectedFilesToOtherPaneForWindows\sync_selected_files_to_other_pane_for_windows\__init__.py
C:\...\Plugins\User\FManSyncSelectedFilesToOtherPaneForWindows\sync_selected_files_to_other_pane_for_windows\__init__.py

Only the second one is used. Please remove one of them.
```

The alert is a warning, not a refusal: loading continues and the second copy
wins, exactly as before. Fix it by deleting one of the two plugin directories,
then restarting fman or running *Reload plugins*.

The same alert appears if a plugin's package name collides with a module fman
has already imported — a package called `json` or `core`, say. The two paths
in the message tell the two cases apart.

### Why the alert exists

Duplicate package names used to surface as a crash instead:

```
Command 'ReloadPlugins' raised error.
KeyError: 'sync_selected_files_to_other_pane_for_windows'
```

Unloading a plugin removes its package from `sys.modules`. With the name
shared, the first unload removed the single entry and the second one found
nothing — and the `KeyError` aborted the whole reload, leaving the remaining
plugins half-unloaded. Unloading now tolerates an already-removed package, and
the collision is reported at load time, where it can name both paths.

## Where the code is

- `src/main/python/fman/impl/plugins/plugin.py` — `ExternalPlugin`: loading a
  plugin directory, scanning its packages for classes to register,
  `_report_if_package_name_taken`, and the unload actions.
- `src/main/python/fman/impl/plugins/__init__.py` — `PluginSupport`, which
  holds the loaded plugins and backs `fman.load_plugin` / `fman.unload_plugin`.
- `src/main/resources/base/Plugins/Core/core/commands/plugins.py` —
  `InstallPlugin`, `ListPlugins`, `RemovePlugin`, `ReloadPlugins` and
  `PreservePanePaths`.
