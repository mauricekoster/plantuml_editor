from PyQt5.QtWidgets import QDialog, QLineEdit, QFileDialog
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot, qDebug, QSettings

from SettingsConstants import *


class LogDialog(QDialog):

    def __init__(self, log, parent):
        super(LogDialog, self).__init__(parent)

        self.ui = loadUi('LogDialog.ui', self)

        self.ui.logViewer.setText(log)
