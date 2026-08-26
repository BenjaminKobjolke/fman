"""The recordable demo scripts, keyed by ``--automation-demo <id>``.

Split out of ``demo.py`` so the player stays readable next to a registry that
grows with every recorded chapter. See ``docs/DEMOS.md`` for how to record
these and what each one is for.

Both panes are already positioned by the trailing paths on the command line
(``tools/create_media/run_fman_demo.bat``), so a script only drives the UI.
Three things every script here depends on:

- **Pane order.** ``core.Name.get_sort_value`` sorts directories first, then
  case-insensitively and naturally, so the seeded folder reads changelog.txt,
  config.json, data.csv, dummy.mp4, dummy_1..dummy_10.jpg, notes.md,
  readme.md, todo.txt - ``dummy.mp4`` before ``dummy_1.jpg`` because ``.``
  sorts before ``_``. Every ``Down`` count below is written against that.
- **Prompt timing.** ``Prompt`` selects its prefilled text only on its second
  ``paintEvent``, so every step that types into one waits >= 1.6 s first.
- **Return is only ever pressed** on a directory, on a ``.zip`` (which
  ``ArchiveOpenListener`` rewrites into "open directory"), or inside a
  dialog. Pressing it on a ``.jpg``/``.mp4`` would launch the Windows default
  application on top of the recording.
"""

from automated_screenshot_connector import (
	Command, DemoScript, Pause, PressKey, Screenshot, TypeText,
)

# Every recording starts translucent, so fman is shown the way it is meant to
# be used and the overview's opacity chapter has something to move away from.
# Forced in application_context._run_demo rather than read from the demo
# profile: a take must never inherit whatever the recordist last picked.
DEMO_OPACITY = 0.8

# The themes demo has no entry in DEMOS: its steps are built per run from the
# themes that are actually installed, so a new ``Themes/*.json`` reaches the
# recording without an edit here. See ``build_themes_script``.
THEMES_DEMO_ID = 2
# How long a theme stays on screen before its still is taken - and, once the
# stills are joined by tools/create_media/build_themes.py, how long it is on
# screen in the GIF.
THEME_HOLD_S = 2.0

DEMOS = {
	1: DemoScript(
		id=1,
		name='overview',
		steps=(
			Pause(0.8),
			Screenshot('panes'),
			# Preview a file in the OTHER pane with fman's internal viewer,
			# while the left pane's list stays visible. Row 0 sorts to the
			# video; one Down lands on the first image.
			PressKey('Down'), Pause(0.4),
			# Open the palette, then type the command + Return to run it.
			PressKey('Ctrl+Shift+P'), Pause(0.5),
			Command('view in other'),  # palette alias 'View in other pane'
			Pause(1.0),
			Screenshot('view-image'),
			# Inline name filter: typing activates fman's FilterBar.
			TypeText('dummy_1'), Pause(0.6),
			Screenshot('filter'),
			PressKey('Escape'), Pause(0.3),
			# A real command run from the palette: select every file.
			PressKey('Ctrl+Shift+P'), Pause(0.5),
			Command('select all'),
			Pause(0.8),
			Screenshot('select-all'),
			Pause(1.0),
			# Window opacity is palette-only (no default key binding), so the
			# palette is the only way to show it at all. 'Opacity' is an alias
			# of Set window opacity. The window already records at
			# DEMO_OPACITY, so the picker goes the other way first: '100'
			# matches just the '100%' preset, '80' just the '80%' one.
			PressKey('Ctrl+Shift+P'), Pause(0.5),
			Command('opacity'), Pause(1.2),
			Command('100'), Pause(1.8),
			# A few moves at full opacity, so the difference reads in motion
			# and not only in a still frame.
			PressKey('Ctrl+D'), Pause(0.8),
			PressKey('Down'), Pause(0.5),
			PressKey('Down'), Pause(0.5),
			PressKey('Up'), Pause(1.0),
			# ... and back to where the recording started.
			PressKey('Ctrl+Shift+P'), Pause(0.5),
			Command('opacity'), Pause(1.2),
			Command('80'), Pause(1.8),
		),
	),
	# ---------------------------------------------------------------------
	# Chapters of the README's feature tour. Recorded separately and joined
	# by tools/create_media/build_tour.py, because the recorder holds every
	# frame in RAM (~30 MB per second at 10 fps) and aborts a single demo at
	# 300 s. They emit no Screenshot steps on purpose: those only write PNG
	# stills, which the tour doesn't need, and the tool's no-event watchdog
	# is satisfied by demo_started alone at these lengths.
	# ---------------------------------------------------------------------
	3: DemoScript(
		id=3,
		name='tour-a-panes',
		steps=(
			Pause(1.5),
			PressKey('Down'), Pause(0.5),
			PressKey('Down'), Pause(0.5),
			PressKey('Down'), Pause(0.5),
			PressKey('Down'), Pause(0.8),
			# Insert selects and advances - the orthodox file-manager key.
			PressKey('Ins'), Pause(0.6),
			PressKey('Ins'), Pause(0.6),
			PressKey('Ins'), Pause(1.2),
			PressKey('Ctrl+D'), Pause(1.0),   # deselect again
			PressKey('Ctrl+A'), Pause(1.4),   # ... and select everything
			PressKey('F5'), Pause(1.8),       # Copy, prefilled with the right pane
			PressKey('Return'), Pause(4.0),   # ~20 MB, dummy.mp4 included
			PressKey('Ctrl+D'), Pause(1.0),
			PressKey('Tab'), Pause(1.2),      # over to the copies
			PressKey('Ctrl+R'), Pause(1.5),   # re-list, so the filter sees them
			TypeText('dummy_1'), Pause(1.8),  # inline type-to-filter
			PressKey('Escape'), Pause(1.0),
			TypeText('read'), Pause(1.8),
			PressKey('Escape'), Pause(1.0),
			PressKey('Ctrl+F2'), Pause(1.8),  # sort by size
			PressKey('Ctrl+F1'), Pause(1.4),  # back to name
			PressKey('Tab'), Pause(1.2),
		),
	),
	4: DemoScript(
		id=4,
		name='tour-b-organize',
		steps=(
			Pause(1.5),
			PressKey('F7'), Pause(1.8),       # prompt prefilled with the stem
			TypeText('documents'), Pause(1.0),
			PressKey('Return'), Pause(1.6),   # created, cursor placed on it
			PressKey('Down'), Pause(0.6),
			PressKey('Ins'), Pause(0.6),
			PressKey('Ins'), Pause(0.6),
			PressKey('Ins'), Pause(1.2),      # the three text files
			PressKey('F6'), Pause(1.8),
			# A bare name in the Move prompt resolves against the SOURCE pane,
			# and the target already exists as a directory, so moving into it
			# needs no further confirmation.
			TypeText('documents'), Pause(1.0),
			PressKey('Return'), Pause(2.5),
			PressKey('Home'), Pause(0.8),     # directories sort first
			PressKey('Return'), Pause(1.8),   # step into it
			PressKey('Shift+F6'), Pause(1.6), # inline editor, extension kept
			TypeText('history'), Pause(1.0),
			PressKey('Return'), Pause(1.8),
			PressKey('Backspace'), Pause(2.0),
			Pause(1.0),
		),
	),
	5: DemoScript(
		id=5,
		name='tour-c-viewers',
		steps=(
			Pause(1.2),
			PressKey('Down'), Pause(0.35),
			PressKey('Down'), Pause(0.35),
			PressKey('Down'), Pause(0.35),
			PressKey('Down'), Pause(0.8),     # dummy_1.jpg
			PressKey('Ctrl+Shift+P'), Pause(1.0),
			Command('view file'), Pause(2.2),
			PressKey('Alt+Up'), Pause(0.7),
			PressKey('Alt+Up'), Pause(1.4),
			# Ctrl+Shift+P inside a viewer opens that viewer's OWN palette -
			# the global one can't reach a viewer while the list is hidden.
			PressKey('Ctrl+Shift+P'), Pause(1.2),
			Command('next'), Pause(2.2),      # on to dummy_2.jpg
			PressKey('Ctrl+Shift+P'), Pause(1.0),
			Command('fit'), Pause(1.4),       # Fit to window, clears the saved zoom
			PressKey('Escape'), Pause(1.2),
			PressKey('Home'), Pause(0.8),     # changelog.txt
			PressKey('Ctrl+Shift+P'), Pause(1.0),
			Command('view file'), Pause(2.0),
			PressKey('Ctrl+Shift+P'), Pause(1.0),
			Command('edit'), Pause(1.0),
			PressKey('Ctrl+End'), Pause(0.5),
			PressKey('Return'), Pause(0.3),   # a newline; TypeText can't carry one
			TypeText('Edited in fman'), Pause(1.3),
			PressKey('Ctrl+Shift+P'), Pause(1.0),
			Command('save'), Pause(1.5),      # straight to disk, no dialog
			PressKey('Ctrl+Shift+P'), Pause(1.0),
			Command('exit'), Pause(1.2),      # Escape doesn't close in edit mode
		),
	),
	6: DemoScript(
		id=6,
		name='tour-d-video',
		steps=(
			Pause(1.2),
			PressKey('Down'), Pause(0.3),
			PressKey('Down'), Pause(0.3),
			PressKey('Down'), Pause(0.8),     # dummy.mp4
			PressKey('Ctrl+Shift+P'), Pause(1.0),
			Command('view file'), Pause(3.5), # libmpv embeds, then plays
			Pause(1.5),
			PressKey('Space'), Pause(1.6),    # pause
			PressKey('Space'), Pause(1.4),    # play
			PressKey('Right'), Pause(1.0),    # seek +5 s
			PressKey('Right'), Pause(1.0),
			PressKey('Up'), Pause(1.4),       # volume +5, with mpv's OSD
			PressKey('Escape'), Pause(1.2),
			# The same viewer, but in the OTHER pane: the list stays usable,
			# so arrowing down keeps previewing.
			PressKey('Down'), Pause(0.6),
			PressKey('Ctrl+Shift+P'), Pause(1.0),
			Command('view in other'), Pause(3.0),
			PressKey('Down'), Pause(1.5),
			PressKey('Down'), Pause(1.5),
			Pause(1.2),
		),
	),
	7: DemoScript(
		id=7,
		name='tour-e-archives',
		steps=(
			Pause(1.2),
			PressKey('Down'), Pause(0.35),
			PressKey('Down'), Pause(0.35),
			PressKey('Down'), Pause(0.35),
			PressKey('Down'), Pause(0.8),
			PressKey('Ins'), Pause(0.6),
			PressKey('Ins'), Pause(0.6),
			PressKey('Ins'), Pause(1.2),      # dummy_1..3.jpg
			PressKey('Alt+F5'), Pause(1.8),   # Pack, suggesting the right pane
			# Replace the whole suggestion: a bare name keeps the archive here,
			# so extracting it into the empty right pane can't hit a conflict.
			PressKey('Ctrl+A'), Pause(0.5),
			TypeText('images.zip'), Pause(1.0),
			PressKey('Return'), Pause(3.5),   # 7za builds it
			# The pane doesn't re-list itself once the archive appears, so the
			# filter below would find nothing without this reload.
			PressKey('Ctrl+R'), Pause(1.5),
			TypeText('ima'), Pause(1.8),      # filter down to the new archive
			PressKey('Return'), Pause(2.5),   # ... and step inside it
			PressKey('F5'), Pause(1.8),       # copy back out of the archive
			PressKey('Return'), Pause(2.5),
			PressKey('Backspace'), Pause(2.0),
			PressKey('Ctrl+Shift+P'), Pause(1.4),
			# Typed as two word-prefixes, to show the palette's fuzzy matching
			# before the command runs.
			TypeText('comp dir'), Pause(2.0),
			PressKey('Return'), Pause(2.0),
			PressKey('Return'), Pause(1.8),   # dismiss the result dialog
			Pause(1.2),
		),
	),
}

def build_themes_script(names):
	"""The themes demo for the installed themes `names`, one still each.

	Only the stills are used: ``fman.json`` gives this demo no video format,
	and ``build_themes.py`` joins the PNGs into the README's GIF. That is why
	the command palette may be on screen between the holds - nothing but the
	``Screenshot`` moments is ever recorded.

	``Command(name)`` types the theme's full name into the quicksearch, which
	matches with ``contains_chars``: a short name is a subsequence of a longer
	one ('Dark' also matches 'Gruvbox Dark'), and ties break by the sorted
	`names` order - which today always puts the exact name first. A future
	theme sorting *before* one whose name it contains ('Ayu Dark' before
	'Dark') would steal the query, so check the stills, not just how many
	were written.

	Length: ~7 s per theme (the name is typed a character at a time) against
	the tool's 300 s cap, i.e. ~40 themes. Its 60 s no-event watchdog is fed
	by the per-theme ``Screenshot``.
	"""
	steps = [
		Pause(1.0),
		# Pin the opacity before the first switch. The recording starts at
		# DEMO_OPACITY, but a theme may carry an `opacity` of its own, so
		# every switch below could move it. These stills are about color,
		# and a translucent window blends the desktop into the very colors
		# they are meant to show.
		PressKey('Ctrl+Shift+P'), Pause(0.6),
		Command('opacity'), Pause(1.2),
		Command('100'), Pause(1.2),
	]
	for name in names:
		steps += [
			PressKey('Ctrl+Shift+P'), Pause(0.6),
			Command('select theme'), Pause(1.2),
			Command(name), Pause(THEME_HOLD_S),
			Screenshot(name),
			# The tool saves a still from the next frame it *captures*, so
			# the palette has to stay closed for a moment afterwards.
			Pause(1.2),
		]
	return DemoScript(id=THEMES_DEMO_ID, name='themes', steps=tuple(steps))

def get_script(demo_id, theme_names):
	"""The DemoScript for `demo_id`, or None if there is no such demo."""
	if demo_id == THEMES_DEMO_ID:
		return build_themes_script(theme_names)
	return DEMOS.get(demo_id)

def demo_ids():
	return sorted(set(DEMOS) | {THEMES_DEMO_ID})
