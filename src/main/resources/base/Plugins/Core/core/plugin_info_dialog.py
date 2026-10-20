"""Show a plugin description before installing it."""
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import (
	QApplication, QDialog, QDialogButtonBox, QTextBrowser,
	QVBoxLayout,
)

from fman.impl.util.qt.thread import run_in_main_thread
from fman.impl.widgets import MessageBox

BACK_LABEL = 'Back'
INSTALL_LABEL = 'Install'


@run_in_main_thread
def show_plugin_info(title, markdown):
	dialog = _PluginInfoDialog(title, markdown, QApplication.activeWindow())
	return dialog.exec_() == QDialog.Accepted


class _PluginInfoDialog(QDialog):
	def __init__(self, title, markdown, parent):
		super().__init__(parent)
		self.setWindowTitle(title)
		layout = QVBoxLayout(self)
		self._description = QTextBrowser(self)
		self._description.setMarkdown(markdown)
		self._description.setOpenExternalLinks(True)
		layout.addWidget(self._description)

		buttons = QDialogButtonBox(self)
		buttons.addButton(BACK_LABEL, QDialogButtonBox.RejectRole)
		install = buttons.addButton(INSTALL_LABEL, QDialogButtonBox.AcceptRole)
		install.setDefault(True)
		install.setFocus()
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)
		layout.addWidget(buttons)

		metrics = self.fontMetrics()
		width = metrics.averageCharWidth() * 70
		height = metrics.lineSpacing() * 25
		self.resize(QSize(width, height))
		available = QApplication.desktop().availableGeometry(self)
		self.resize(min(width, int(available.width() * MessageBox._MAX_SCREEN_SHARE)),
			min(height, int(available.height() * MessageBox._MAX_SCREEN_SHARE)))
