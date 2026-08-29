"""
Shared font-size clamp for widget zoom features: pane font size
(core/commands/pane_view.py) and the text viewer's own zoom
(core/textviewer.py). Kept in its own module (rather than importing one
feature from the other) since core/commands/__init__.py imports
core/textviewer.py at module load - the reverse import would be circular.
"""

MIN_FONT_SIZE = 6
MAX_FONT_SIZE = 40

def clamp_font_size(current, delta):
	return max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, current + delta))
