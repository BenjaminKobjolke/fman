"""
The status-bar line every in-pane viewer reports through - the text, image and
video viewers (core/textviewer.py, core/imageviewer.py, core/videoviewer.py)
and their helper modules. A viewer action that changes something the user
cannot otherwise see (a reload of an unchanged file, entering edit mode, a
zoom step) confirms it here; see docs/viewers/FILE_VIEWERS.md.

Its own module rather than a function in core/viewer_navigation.py because the
zoom modules import it too, and viewer_navigation.py already carries an import
cycle with core/viewers.py (see _category there). Importing nothing but fman,
this module can't add another.
"""
from fman import show_status_message

# fman's status bar has a single message slot, so a viewer message that never
# expired would keep describing a viewer the user has long since closed.
_TIMEOUT_SECS = 3

def viewer_status(text):
	show_status_message(text, timeout_secs=_TIMEOUT_SECS)
