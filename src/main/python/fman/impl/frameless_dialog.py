"""
A dialog without a title bar, shown when the main window hides its own: an
outline (styles.qss, `*[frameless="true"]`) so it does not blend into the
window behind it, and wider margins so the content keeps off that outline.

The margins come from the app's style (view.ProxyStyle asks extra_margin(...)),
not from `padding` in styles.qss: Qt ignores padding on dialogs, and
QProgressDialog places its children by hand using the style's layout margins.
Not from a style of the dialog's own either: its buttons would lose the
theme's stylesheet.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QStyle

_PROPERTY = 'frameless'

_EXTRA_MARGIN = 8

_MARGINS = (
	QStyle.PM_LayoutLeftMargin, QStyle.PM_LayoutTopMargin,
	QStyle.PM_LayoutRightMargin, QStyle.PM_LayoutBottomMargin
)

def make_frameless(dialog):
	# Set the flag before show(), so Qt does not recreate the native window.
	dialog.setWindowFlag(Qt.FramelessWindowHint)
	dialog.setProperty(_PROPERTY, True)

def extra_margin(metric, widget):
	if metric in _MARGINS and widget is not None and \
			widget.property(_PROPERTY):
		return _EXTRA_MARGIN
	return 0
