from PySide6.QtWidgets import QDialog, QLineEdit, QFileDialog
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import qDebug, QSettings

from SettingsConstants import *


class LogDialog(QDialog):

    def __init__(self, log, parent):
        super(LogDialog, self).__init__(parent)

        self.ui = QUiLoader.load('LogDialog.ui', self)

        self.ui.logViewer.setText(log)
