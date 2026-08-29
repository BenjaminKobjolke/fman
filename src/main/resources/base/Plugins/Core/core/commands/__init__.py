"""fman's built-in commands, grouped one module per concern.

Nothing is defined here any more: this file only re-exports. fman's plugin
loader (src/main/python/fman/impl/plugins/plugin.py) discovers commands by
walking `dir(core)` for classes, so a command counts as registered exactly
when it is reachable as an attribute of the top-level `core` package - which
is what `core/__init__.py`'s `from core.commands import *` plus the star
imports below arrange. Which module a command is defined in is invisible to
the loader, to key bindings and to 'Command Titles.json'; the class name is
not - that is where the command name comes from.

`import *` skips underscore-prefixed names, so a helper one module borrows
from another has to be imported explicitly, by that module, from its owner.
core/commands/util.py holds the ones several modules need at once, because
none of those modules may import a sibling that imports it back.
"""
from .app import *
from .archives import *
from .clipboard import *
from .columns import *
from .deletion import *
from .editor import *
from .external import *
from .file_properties import *
from .goto import *
from .hidden_files import *
from .navigation import *
from .open_with import *
from .opening import *
from .pack import *
from .palette import *
from .pane_view import *
from .places import *
from .plugins import *
from .release_notes import *
from .rename import *
from .theme import *
from .transfer import *
from .window import *
