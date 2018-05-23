from PyQt5.QtWidgets import QDialog, QLineEdit, QFileDialog
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot, qDebug


class PreferencesDialog(QDialog):
    def __init__(self, file_cache, parent):
        super(PreferencesDialog, self).__init__(parent)
        self.file_cache = file_cache

        self.ui = loadUi('PreferencesDialog.ui', self)

        self.rejected.connect(self.on_rejected)

        self.ui.customJavaPathEdit.setText('Hello world!')

    def on_rejected(self):
        qDebug("REJECT")

    @pyqtSlot()
    def on_customJavaPathButton_clicked(self):
        # qDebug("on_customJavaPathButton_clicked")
        file_name = QFileDialog.getOpenFileName(self,
                                                 self.tr("Select Java executable"),
                                                 self.ui.customJavaPathEdit.text())

        file_name = file_name[0]
        if file_name:
            self.ui.customJavaPathEdit.setText(file_name)
            self.ui.customJavaRadio.setChecked(True)

    def read_settings(self):
        pass

    def write_settings(self):
        pass
