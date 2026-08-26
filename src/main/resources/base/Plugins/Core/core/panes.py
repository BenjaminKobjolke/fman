"""
Reloading the open panes. Model#reload() clears the FS cache for a pane's
location, which is where the icons built under the old icon set, color or
network setting are held - so every command that changes which icon a file
gets has to call this, or the panes keep drawing the old ones.

Clearing that cache is necessary but not sufficient: the reload's diff drops
the freshly built icons unless the icon generation moved too. IconProvider
takes care of that - see invalidate_icons() in fman.impl.model.table.
"""

def reload_panes(window):
	for pane in window.get_panes():
		pane.reload()
