from PySide6 import QtCore
from PySide6.QtWidgets import QDialog, QLineEdit, QFileDialog
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import qDebug, QSettings, QProcess

from LogDialog import LogDialog
from SettingsConstants import *


class PreferencesDialog(QDialog):
    def __init__(self, file_cache, parent):
        super(PreferencesDialog, self).__init__(parent)
        self.file_cache = file_cache

        self.ui = QUiLoader.loadUi('PreferencesDialog.ui', self)

        self.ui.defaultJavaRadio.setText("Default ({})".format(SETTINGS_CUSTOM_JAVA_PATH_DEFAULT))
        self.ui.defaultPlantUmlRadio.setText("Default ({})".format(SETTINGS_CUSTOM_PLANTUML_PATH_DEFAULT))
        self.ui.defaultGraphvizRadio.setText("Default ({})".format(SETTINGS_CUSTOM_GRAPHVIZ_PATH_DEFAULT))
        self.rejected.connect(self.on_rejected)

    def on_rejected(self):
        qDebug("REJECT")

    @QtCore.Slot()
    def on_customJavaPathButton_clicked(self):
        # qDebug("on_customJavaPathButton_clicked")
        file_name = QFileDialog.getOpenFileName(self,
                                                self.tr("Select Java executable"),
                                                self.ui.customJavaPathEdit.text())

        file_name = file_name[0]
        if file_name:
            self.ui.customJavaPathEdit.setText(file_name)
            self.ui.customJavaRadio.setChecked(True)

    @QtCore.Slot()
    def on_customPlantUmlButton_clicked(self):
        file_name = QFileDialog.getOpenFileName(self,
                                                self.tr("Select plantuml.jar"),
                                                self.ui.customPlantUmlEdit.text())

        file_name = file_name[0]
        if file_name:
            self.ui.customPlantUmlEdit.setText(file_name)
            self.ui.customPlantUmlRadio.setChecked(True)

    @QtCore.Slot()
    def on_customGraphvizButton_clicked(self):
        file_name = QFileDialog.getOpenFileName(self,
                                                self.tr("Select Graphviz dot executable"),
                                                self.ui.customGraphvizEdit.text())

        file_name = file_name[0]
        if file_name:
            self.ui.customGraphvizEdit.setText(file_name)
            self.ui.customGraphvizRadio.setChecked(True)

    @QtCore.Slot()
    def on_checkExternalPrograms_clicked(self):
        self.check_external_programs()

    def read_settings(self):
        settings = QSettings()
        settings.beginGroup(SETTINGS_MAIN_SECTION)

        if settings.value(SETTINGS_USE_CUSTOM_JAVA,
                          SETTINGS_USE_CUSTOM_JAVA_DEFAULT, bool):
            self.ui.customJavaRadio.setChecked(True)
        else:
            self.ui.defaultJavaRadio.setChecked(True)
        self.ui.customJavaPathEdit.setText(settings.value(SETTINGS_CUSTOM_JAVA_PATH,
                                                          SETTINGS_CUSTOM_JAVA_PATH_DEFAULT))

        if settings.value(SETTINGS_USE_CUSTOM_PLANTUML,
                          SETTINGS_USE_CUSTOM_PLANTUML_DEFAULT, bool):
            self.ui.customPlantUmlRadio.setChecked(True)
        else:
            self.ui.defaultPlantUmlRadio.setChecked(True)
        self.ui.customPlantUmlEdit.setText(settings.value(SETTINGS_CUSTOM_PLANTUML_PATH,
                                                          SETTINGS_CUSTOM_PLANTUML_PATH_DEFAULT))

        if settings.value(SETTINGS_USE_CUSTOM_GRAPHVIZ,
                          SETTINGS_USE_CUSTOM_GRAPHVIZ_DEFAULT, bool):
            self.ui.customGraphvizRadio.setChecked(True)
        else:
            self.ui.defaultGraphvizRadio.setChecked(True)
        self.ui.customGraphvizEdit.setText(settings.value(SETTINGS_CUSTOM_GRAPHVIZ_PATH,
                                                          SETTINGS_CUSTOM_GRAPHVIZ_PATH_DEFAULT))

        settings.endGroup()

    def write_settings(self):
        settings = QSettings()
        settings.beginGroup(SETTINGS_MAIN_SECTION)

        settings.setValue(SETTINGS_USE_CUSTOM_JAVA, self.ui.customJavaRadio.isChecked())
        settings.setValue(SETTINGS_CUSTOM_JAVA_PATH, self.ui.customJavaPathEdit.text())

        settings.setValue(SETTINGS_USE_CUSTOM_PLANTUML, self.ui.customPlantUmlRadio.isChecked())
        settings.setValue(SETTINGS_CUSTOM_PLANTUML_PATH, self.ui.customPlantUmlEdit.text())

        settings.setValue(SETTINGS_USE_CUSTOM_GRAPHVIZ, self.ui.customGraphvizRadio.isChecked())
        settings.setValue(SETTINGS_CUSTOM_GRAPHVIZ_PATH, self.ui.customGraphvizEdit.text())
        settings.endGroup()

    def check_external_programs(self):
        qDebug("Check external programs")
        log = ""
        java_path = self.ui.customJavaPathEdit.text() \
            if self.ui.customJavaRadio.isChecked() \
            else SETTINGS_CUSTOM_JAVA_PATH_DEFAULT

        graphviz_path = self.ui.customGraphvizEdit.text() \
            if self.ui.customGraphvizRadio.isChecked() \
            else SETTINGS_CUSTOM_GRAPHVIZ_PATH_DEFAULT

        invalid_path_log = "<font color=\"red\">invalid path</font>"

        log += "Testing Java executable <tt>{}</tt>: ".format(java_path)
        is_java_ok = False
        if os.path.exists(java_path):
            is_java_ok, log = self.check_external_program(java_path, ["-version"], log)
        else:
            log += invalid_path_log

        log += "<p>"
        log += "Testing graphiz/dot <tt>{}</tt>: ".format(graphviz_path)

        is_graphviz_ok = False
        if not os.path.exists(graphviz_path):
            log += invalid_path_log
        else:
            is_graphviz_ok, log = self.check_external_program(graphviz_path, ["-V"], log,
                                                              ".*dot - graphviz version.*")

        if is_java_ok and is_graphviz_ok:
            pass

        self.show_log(log)

    def check_external_program(self, command, args, log, validator=None):
        process = QProcess()
        process.start(command, args)
        process.waitForFinished()

        output = process.readAllStandardOutput() + process.readAllStandardError()

        if process.exitCode() == 0:
            validation_ok = True

            if validation_ok:
                log += "<b><font color=\"green\">OK</font></b>"
                return True, log

        log += "<font color=\"red\">FAILED</font>"
        log += "<pre>"
        log += output
        log += "</pre>"
        return False, log

    def show_log(self, log):
        if log:
            logDialog = LogDialog(log, self)
            logDialog.setModal(True)
            logDialog.exec_()
