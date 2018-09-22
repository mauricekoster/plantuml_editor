import os
import sys
import hashlib

from PyQt5.Qt import Qt, QApplication
from PyQt5.QtCore import QT_TRANSLATE_NOOP, qDebug, QTimer, QSettings, QProcess
from PyQt5.QtCore import QFileInfo
from PyQt5.QtGui import QIcon, QKeySequence, QFontMetrics, QPixmap, QClipboard
from PyQt5.QtWidgets import QMainWindow, QScrollArea, QAction, QDockWidget
from PyQt5.QtWidgets import qApp, QLabel, QMessageBox, QFileDialog, QDialog

from ImageFormat import ImageFormat
from PreferencesDialog import PreferencesDialog
from PreviewWindow import PreviewWindow, Mode
from RecentDocuments import RecentDocuments
from TextEdit import TextEdit
from FileCache import FileCache, FileCacheItem
from SettingsConstants import *

ASSISTANT_ITEM_DATA_ROLE = Qt.UserRole
ASSISTANT_ITEM_NOTES_ROLE = Qt.UserRole + 1

MAX_RECENT_DOCUMENT_SIZE = 10
STATUS_BAR_TIMEOUT = 3000  # in miliseconds
TITLE_FORMAT_STRING = "{0}[*] - {1}"
EXPORT_TO_MENU_FORMAT_STRING = QT_TRANSLATE_NOOP("MainWindow", "Export to {0}")
EXPORT_TO_LABEL_FORMAT_STRING = QT_TRANSLATE_NOOP("MainWindow", "Export to: {0}")
AUTO_REFRESH_STATUS_LABEL = QT_TRANSLATE_NOOP("MainWindow", "Auto-refresh")
CACHE_SIZE_FORMAT_STRING = QT_TRANSLATE_NOOP("MainWindow", "Cache: {0}")
ASSISTANT_ICON_SIZE = (128, 128)


def compute_md5_hash(my_string):
    m = hashlib.md5()
    m.update(my_string.encode('utf-8'))
    return m.hexdigest()


def resource_path(path):
    if getattr(sys, 'frozen', False):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)

    return os.path.join(basedir, path)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1200, 800)
        self.setWindowTitle(TITLE_FORMAT_STRING.format("", qApp.applicationName()))
        self.setWindowIcon(QIcon(resource_path('icons/plantuml.png')))

        self.has_valid_paths = False
        self.process = None
        self.current_image_format = ImageFormat.PngFormat
        self.needs_refresh = False
        self.refresh_on_save = False

        self.image_format_names = {
            ImageFormat.SvgFormat: "svg",
            ImageFormat.PngFormat: "png",
        }

        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.refresh)

        self.use_cache = False
        self.cache = FileCache(0, self)
        self.cached_image = None

        self.document_path = None
        self.export_path = None

        # TODO: Connect signal to recent_documents
        self.recent_documents = RecentDocuments(MAX_RECENT_DOCUMENT_SIZE, self)

        self.last_key = None
        self.last_dir = os.path.dirname(os.path.realpath(__file__))

        self.editor = TextEdit(self)
        self.editor.document().contentsChanged.connect(self.on_editor_changed)

        self.setCentralWidget(self.editor)

        self.create_dock_windows()
        self.create_actions()
        self.create_menus()
        self.create_tool_bars()
        self.create_status_bar()

        self.setUnifiedTitleAndToolBarOnMac(True)

        # TODO: Assistant signal mapper

        self.read_settings()

        # TODO: Single application?

    def closeEvent(self, event):
        if self.maybe_save():
            self.write_settings()
            event.accept()
        else:
            event.ignore()

    def create_dock_diagram(self):
        dock = QDockWidget(self.tr("Diagram"), self)
        dock.setMinimumWidth(300)

        self.image_widget = PreviewWindow(dock)

        self.image_widget_scrollarea = QScrollArea()
        self.image_widget_scrollarea.setWidget(self.image_widget)
        self.image_widget_scrollarea.setAlignment(Qt.AlignCenter)
        self.image_widget_scrollarea.setWidgetResizable(True)

        dock.setWidget(self.image_widget_scrollarea)
        dock.setObjectName("diagram")
        return dock

    def create_dock_windows(self):
        self.addDockWidget(Qt.RightDockWidgetArea, self.create_dock_diagram())

    def create_actions(self):
        # File menu actions
        self.new_document_action = QAction(QIcon.fromTheme("document-new"),
                                           self.tr("&New document"), self)
        self.new_document_action.setShortcut(QKeySequence.New)
        self.new_document_action.triggered.connect(self.new_document)

        self.open_document_action = QAction(QIcon.fromTheme("document-open"),
                                            self.tr("&Open document"), self)
        self.open_document_action.setShortcut(QKeySequence.Open)
        self.open_document_action.triggered.connect(self.on_open_document_triggered)

        self.save_document_action = QAction(QIcon.fromTheme("document-save"),
                                            self.tr("&Save document"), self)
        self.save_document_action.setShortcut(QKeySequence.Save)
        self.save_document_action.triggered.connect(self.on_save_document_triggered)

        self.save_as_document_action = QAction(QIcon.fromTheme("document-save-as"),
                                               self.tr("Save as..."), self)
        self.save_as_document_action.setShortcut(QKeySequence.SaveAs)
        self.save_as_document_action.triggered.connect(self.on_save_as_document_triggered)

        self.export_image_action = QAction(self.tr(EXPORT_TO_MENU_FORMAT_STRING.format("")), self)
        self.export_image_action.setShortcut(Qt.CTRL + Qt.Key_E)
        self.export_image_action.triggered.connect(self.on_export_image_action_triggered)

        self.export_as_image_action = QAction(self.tr("Export as ..."), self)
        self.export_as_image_action.setShortcut(Qt.CTRL + Qt.SHIFT + Qt.Key_E)
        self.export_as_image_action.triggered.connect(self.on_export_as_image_action_triggered)

        self.quit_action = QAction(QIcon.fromTheme("application-exit"),
                                   self.tr("&Quit"), self)
        self.quit_action.setShortcuts(QKeySequence.Quit)
        self.quit_action.setStatusTip(self.tr("Quit the application"))
        self.quit_action.triggered.connect(self.close)

        # Edit menu
        self.undo_action = QAction(QIcon.fromTheme("edit-undo"),
                                   self.tr("&Undo"), self)
        self.undo_action.setShortcuts(QKeySequence.Undo)
        self.undo_action.triggered.connect(self.undo)

        self.redo_action = QAction(QIcon.fromTheme("edit-redo"),
                                   self.tr("&Redo"), self)
        self.redo_action.setShortcuts(QKeySequence.Redo)
        self.redo_action.triggered.connect(self.redo)

        self.copy_image_action = QAction(QIcon.fromTheme("copy"),
                                         self.tr("&Copy Image"), self)
        self.copy_image_action.setShortcuts(QKeySequence.Copy)
        self.copy_image_action.triggered.connect(self.copy_image)

        # Tools menu
        self.refresh_action = QAction(QIcon.fromTheme("view-refresh"), self.tr("Refresh"), self)
        self.refresh_action.setShortcuts(QKeySequence.Refresh)
        self.refresh_action.setStatusTip(self.tr("Call PlantUML to regenerate the UML image"))
        self.refresh_action.triggered.connect(self.on_refresh_action_triggered)

        self.auto_refresh_action = QAction(self.tr("Auto-Refresh"), self)
        self.auto_refresh_action.setCheckable(True)
        self.auto_refresh_action.toggled.connect(self.on_auto_refresh_action_toggled)

        self.auto_save_image_action = QAction(self.tr("Auto-Save image"), self)
        self.auto_save_image_action.setCheckable(True)

        # Settings menu
        self.show_main_toolbar_action = QAction(self.tr("Show toolbar"), self)
        self.show_main_toolbar_action.setCheckable(True)

        self.show_status_bar_action = QAction(self.tr("Show statusbar"), self)
        self.show_status_bar_action.setCheckable(True)

        self.preferences_action = QAction(QIcon.fromTheme("preferences-other"), self.tr("Preferences"), self)
        self.preferences_action.triggered.connect(self.on_preferences_action_triggered)

        # Help menu
        self.about_action = QAction(QIcon.fromTheme("help-about"), self.tr("&About"), self)
        self.about_action.setStatusTip(self.tr("Show the application's About box"))
        self.about_action.triggered.connect(self.about)

        self.about_qt_action = QAction(self.tr("About &Qt"), self)
        self.about_qt_action.setStatusTip(self.tr("Show the Qt library's About box"))
        self.about_qt_action.triggered.connect(self.about_qt)

        # Focus actions

        # Assistant actions

        # Zoom actions
        self.zoom_in_action = QAction(QIcon.fromTheme("zoom-in"), self.tr("Zoom In"), self)
        self.zoom_in_action.triggered.connect(self.image_widget.zoom_in)
        self.zoom_out_action = QAction(QIcon.fromTheme("zoom-out"), self.tr("Zoom Out"), self)
        self.zoom_out_action.triggered.connect(self.image_widget.zoom_out)
        self.zoom_original_action = QAction(QIcon.fromTheme("zoom-original"), self.tr("1:1"), self)
        self.zoom_original_action.triggered.connect(self.image_widget.zoom_original)

    def create_menus(self):
        # File menu
        self.file_menu = self.menuBar().addMenu(self.tr("&File"))
        self.file_menu.addAction(self.new_document_action)
        self.file_menu.addAction(self.open_document_action)
        self.file_menu.addAction(self.save_document_action)
        self.file_menu.addAction(self.save_as_document_action)

        # self.file_menu.addSeparator();
        # QMenu * recent_documents_submenu = m_fileMenu->addMenu(tr("Recent Documents"));
        # recent_documents_submenu->addActions(m_recentDocuments->actions());

        self.file_menu.addSeparator();
        self.file_menu.addAction(self.export_image_action);
        # self.file_menu.addAction(m_exportAsImageAction);
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.quit_action)

        # Edit menu
        self.edit_menu = self.menuBar().addMenu(self.tr("&Edit"))
        self.edit_menu.addAction(self.undo_action)
        self.edit_menu.addAction(self.redo_action)
        self.edit_menu.addAction(self.copy_image_action)
        self.edit_menu.addSeparator()
        self.edit_menu.addAction(self.refresh_action)

        # Settings menu
        self.settings_menu = self.menuBar().addMenu(self.tr("&Settings"))
        # self.settings_menu.addAction(m_showMainToolbarAction)
        # self.settings_menu.addAction(m_showStatusBarAction)
        # self.settings_menu.addSeparator()
        # self.settings_menu.addAction(m_showAssistantDockAction)
        # self.settings_menu.addAction(m_showAssistantInfoDockAction)
        # self.settings_menu.addAction(m_showEditorDockAction)
        # self.settings_menu.addSeparator()
        # self.settings_menu.addAction(m_pngPreviewAction)
        # self.settings_menu.addAction(m_svgPreviewAction)
        self.settings_menu.addSeparator()
        self.settings_menu.addAction(self.auto_refresh_action)
        self.settings_menu.addAction(self.auto_save_image_action)
        self.settings_menu.addSeparator()
        self.settings_menu.addAction(self.preferences_action)

        self.zoom_menu = self.menuBar().addMenu(self.tr("&Zoom"))
        self.zoom_menu.addAction(self.zoom_in_action)
        self.zoom_menu.addAction(self.zoom_out_action)
        self.zoom_menu.addAction(self.zoom_original_action)

        # Help menu
        self.menuBar().addSeparator()
        self.help_menu = self.menuBar().addMenu(self.tr("&Help"))
        self.help_menu.addAction(self.about_action)
        self.help_menu.addAction(self.about_qt_action)

    def create_tool_bars(self):
        self.main_tool_bar = self.addToolBar(self.tr("MainToolbar"))
        self.main_tool_bar.setObjectName("main_toolbar")
        self.main_tool_bar.addAction(self.quit_action)
        self.main_tool_bar.addAction(self.new_document_action)
        self.main_tool_bar.addAction(self.open_document_action)
        self.main_tool_bar.addAction(self.save_document_action)
        self.main_tool_bar.addAction(self.save_as_document_action)
        # self.main_tool_bar.addSeparator()
        # self.main_tool_bar.addAction(m_showAssistantDockAction)
        # self.main_tool_bar.addAction(m_showAssistantInfoDockAction)
        # self.main_tool_bar.addAction(m_showEditorDockAction)
        self.main_tool_bar.addSeparator()
        self.main_tool_bar.addAction(self.undo_action)
        self.main_tool_bar.addAction(self.redo_action)
        self.main_tool_bar.addAction(self.copy_image_action)
        self.main_tool_bar.addSeparator()
        self.main_tool_bar.addAction(self.refresh_action)
        self.main_tool_bar.addSeparator()
        self.main_tool_bar.addAction(self.preferences_action)
        #
        # m_zoomToolBar = addToolBar(tr("ZoomToolbar"))
        # m_zoomToolBar->setObjectName("zoom_toolbar")
        # addZoomActions(m_zoomToolBar)

    def create_status_bar(self):
        self.export_path_label = QLabel(self)
        self.export_path_label.setMinimumWidth(200)
        self.export_path_label.setText(self.tr(EXPORT_TO_LABEL_FORMAT_STRING).format(""))
        self.export_path_label.setEnabled(False)

        self.current_image_format_label = QLabel(self)

        font_metrics = QFontMetrics(self.export_path_label.font())
        self.cache_size_label = QLabel(self)
        self.cache_size_label.setMinimumWidth(font_metrics.width(
            self.tr(CACHE_SIZE_FORMAT_STRING).format("#.## Mb")))

        self.auto_refresh_label = QLabel(self)
        self.auto_refresh_label.setText(self.tr(AUTO_REFRESH_STATUS_LABEL))

        self.statusBar().addPermanentWidget(self.export_path_label)
        self.statusBar().addPermanentWidget(self.cache_size_label)
        self.statusBar().addPermanentWidget(self.auto_refresh_label)
        self.statusBar().addPermanentWidget(self.current_image_format_label)

        self.statusBar().showMessage(self.tr("Ready"), STATUS_BAR_TIMEOUT)

    def check_paths(self):
        self.has_valid_paths = os.path.exists(self.java_path) and os.path.exists(self.plantuml_path)

    def read_settings(self, reload=False):
        settings = QSettings()
        settings.beginGroup(SETTINGS_MAIN_SECTION)

        use_custom_java = settings.value(SETTINGS_USE_CUSTOM_JAVA,
                                         SETTINGS_USE_CUSTOM_JAVA_DEFAULT, bool)
        custom_java_path = settings.value(SETTINGS_CUSTOM_JAVA_PATH, SETTINGS_CUSTOM_JAVA_PATH_DEFAULT)
        self.java_path = custom_java_path if use_custom_java else SETTINGS_CUSTOM_JAVA_PATH_DEFAULT

        use_custom_plantuml_path = settings.value(SETTINGS_USE_CUSTOM_PLANTUML,
                                                  SETTINGS_USE_CUSTOM_PLANTUML_DEFAULT, bool)
        custom_plantuml_path = settings.value(SETTINGS_CUSTOM_PLANTUML_PATH,
                                              SETTINGS_CUSTOM_PLANTUML_PATH_DEFAULT)
        self.plantuml_path = custom_plantuml_path if use_custom_plantuml_path else SETTINGS_CUSTOM_PLANTUML_PATH_DEFAULT

        use_custom_graphviz_path = settings.value(SETTINGS_USE_CUSTOM_GRAPHVIZ,
                                                  SETTINGS_USE_CUSTOM_GRAPHVIZ_DEFAULT, bool)
        custom_graphviz_path = settings.value(SETTINGS_CUSTOM_GRAPHVIZ_PATH,
                                              SETTINGS_CUSTOM_GRAPHVIZ_PATH_DEFAULT)
        self.graphviz_path = custom_graphviz_path if use_custom_graphviz_path else SETTINGS_CUSTOM_GRAPHVIZ_PATH_DEFAULT

        self.check_paths()

        value = self.image_format_names[ImageFormat.PngFormat]
        # value = settings.value(SETTINGS_IMAGE_FORMAT,
        #                    self.image_format_names[ImageFormat.PngFormat])
        if value == self.image_format_names[ImageFormat.PngFormat]:
            self.current_image_format = ImageFormat.PngFormat
        else:
            self.current_image_format = ImageFormat.SvgFormat

            # if self.current_image_format == ImageFormat.SvgFormat:
            #     m_svgPreviewAction->setChecked(true);
            # elif self.current_image_format == ImageFormat.PngFormat:
            #     m_pngPreviewAction->setChecked(true);

            # m_currentImageFormatLabel->setText(m_imageFormatNames[m_currentImageFormat].toUpper());

        self.autorefresh_enabled = settings.value(SETTINGS_AUTOREFRESH_ENABLED, 'true') == 'true'
        self.auto_refresh_action.setChecked(self.autorefresh_enabled)
        self.auto_refresh_timer.setInterval(
            settings.value(SETTINGS_AUTOREFRESH_TIMEOUT,
                           int(SETTINGS_AUTOREFRESH_TIMEOUT_DEFAULT)))

        if self.autorefresh_enabled:
            qDebug("starting auto refresh timer")
            self.auto_refresh_timer.start()

        self.auto_refresh_label.setEnabled(self.autorefresh_enabled)

    def write_settings(self):
        qDebug("Settings")
        settings = QSettings()
        qDebug(settings.fileName())

        settings.beginGroup(SETTINGS_MAIN_SECTION)
        settings.setValue("Test", 42)
        settings.endGroup()
        # settings.sync()

    def maybe_save(self):
        if self.editor.document().isModified():

            ret = QMessageBox.warning(self, qApp.applicationName(),
                                      self.tr('The document has been modified.\n'
                                              'Do you want to save your changes?'),
                                      buttons=QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if ret == QMessageBox.Save:
                return self.save_document(self.document_path)
            elif ret == QMessageBox.Cancel:
                return False

        return True

    def make_key_for_document(self, current_document):
        key = "%s.%s" % (compute_md5_hash(current_document),
                         self.image_format_names[self.current_image_format])

        return key

    def refresh_from_cache(self):
        # TODO: Refresh from cache
        return False

    def refresh(self, forced=False):
        qDebug("Refreshing")
        if self.process:
            qDebug("still processing previous refresh. skipping...")
            return

        if not self.needs_refresh and not forced:
            return

        if not self.has_valid_paths:
            qDebug("Please configure paths for Java and PlantUML. Aborting...")
            self.statusBar().showMessage(
                self.tr("Java and/or PlantUML not found. Please set them correctly in the \"Preferences\" dialog!"))
            return

        if not forced and self.refresh_from_cache():
            qDebug("HUH ")
            return

        current_document = self.editor.toPlainText()
        if not current_document.strip():
            qDebug("empty document. skipping...")
            return

        self.needs_refresh = False

        if self.current_image_format == ImageFormat.SvgFormat:
            self.image_widget.set_mode(Mode.SvgMode)
        elif self.current_image_format == ImageFormat.PngFormat:
            self.image_widget.set_mode(Mode.PngMode)

        key = self.make_key_for_document(current_document)

        self.statusBar().showMessage(self.tr("Refreshing..."))

        arguments = ['-jar', self.plantuml_path, '-t%s' % self.image_format_names[self.current_image_format]]

        # if self.use_custom_graphiz:
        #     arguments.extend(["-graphvizdot", self.graphviz_path])
        arguments.extend(["-charset", "UTF-8", "-pipe"])

        self.last_key = key
        qDebug("md5: %s" % key)

        self.process = QProcess(self)

        fi = QFileInfo(self.document_path)
        self.process.setWorkingDirectory(fi.absolutePath())

        self.process.start(self.java_path, arguments)
        if not self.process.waitForStarted():
            qDebug("refresh subprocess failed to start")
            return

        self.process.finished.connect(self.refresh_finished)

        self.process.write(bytearray(current_document, 'utf-8'))
        self.process.closeWriteChannel()

    def refresh_finished(self):
        self.cached_image = self.process.readAll()
        self.image_widget.load(self.cached_image)
        self.process.deleteLater()
        self.process = 0;

        if self.use_cache and self.cache:
            self.cache.add_item(self.cached_image, self.last_key,
                                lambda path, key, cost, date_date, parent: FileCacheItem(path, key, cost, date_date,
                                                                                         parent))

            self.update_cache_size_info()

        self.statusBar().showMessage(self.tr("Refreshed"), STATUS_BAR_TIMEOUT)

    def update_cache_size_info(self):
        # TODO
        pass

    def enable_undo_redo_actions(self):
        document = self.editor.document()
        self.undo_action.setEnabled(document.isUndoAvailable())
        self.redo_action.setEnabled(document.isRedoAvailable())

    def new_document(self):
        if not self.maybe_save():
            return

        self.document_path = None
        self.export_path = None
        self.cached_image = None

        # TODO: Export path
        # m_exportImageAction->setText(tr(EXPORT_TO_MENU_FORMAT_STRING).arg(""));
        # m_exportPathLabel->setText(tr(EXPORT_TO_LABEL_FORMAT_STRING).arg(""));
        # m_exportPathLabel->setEnabled(false);

        text = "@startuml\n\nme -> you: Hello!\n\n@enduml"
        self.editor.setPlainText(text)
        self.setWindowTitle(TITLE_FORMAT_STRING.format(
            self.tr("Untitled"),
            qApp.applicationName()))

        self.setWindowModified(False)
        self.refresh()

        self.enable_undo_redo_actions()

    def on_open_document_triggered(self):
        self.open_document()

    def open_document(self, name=None):
        qDebug("Open document")
        if not self.maybe_save():
            return
        tmp_name = name
        if tmp_name is None or not os.path.exists(tmp_name):
            tmp_name = QFileDialog.getOpenFileName(self,
                                                   self.tr("Select a file to open"),
                                                   self.last_dir,
                                                   "PlantUML (*.puml);; All files (*.*)")
            tmp_name = tmp_name[0]
            if not tmp_name:
                return
            self.last_dir = os.path.dirname(os.path.abspath(tmp_name))

        try:
            with open(tmp_name, 'r', encoding='utf-8') as f:
                content = f.readlines()

        except IOError:
            return

        content = "".join(content)
        self.editor.setPlainText(content)
        self.setWindowModified(False)

        self.document_path = tmp_name
        self.setWindowTitle(TITLE_FORMAT_STRING.format(os.path.basename(tmp_name), qApp.applicationName()))
        self.needs_refresh = True
        self.refresh()
        self.recent_documents.accessing(tmp_name)
        qDebug("Opened file {}".format(tmp_name))

    def on_save_document_triggered(self):
        self.save_document(self.document_path)
        if self.refresh_on_save:
            self.on_refresh_action_triggered()

    def on_save_as_document_triggered(self):
        self.save_document()

    def on_export_image_action_triggered(self):
        qDebug("Export to triggered")
        self.export_image(self.export_path)

    def on_export_as_image_action_triggered(self):
        self.export_image(None)

    def on_preferences_action_triggered(self):
        self.write_settings()
        dialog = PreferencesDialog(self.cache, self)
        dialog.read_settings()
        dialog.setModal(True)
        dialog.exec_()
        result = dialog.result()

        if result == QDialog.Accepted:
            dialog.write_settings()
            self.read_settings(True)

    def save_document(self, name=None):
        qDebug("Saving document {}".format(name))
        file_path = name
        if file_path is None:
            file_path = QFileDialog.getSaveFileName(self,
                                                    self.tr("Select where to store the document"),
                                                    self.last_dir,
                                                    "PlantUML (*.puml);; All Files (*.*)")
            file_path = file_path[0]
            if not file_path:
                return False
            self.last_dir = os.path.dirname(os.path.abspath(file_path))

        qDebug("saving document in: {}".format(file_path))
        with open(file_path, 'wb') as f:
            f.write(self.editor.toPlainText().encode('utf-8'))

        self.document_path = file_path
        self.setWindowTitle(TITLE_FORMAT_STRING.format(os.path.basename(file_path), qApp.applicationName()))
        self.statusBar().showMessage(self.tr("Document saved in {}".format(file_path)), STATUS_BAR_TIMEOUT)
        self.recent_documents.accessing(file_path)

        if self.auto_save_image_action.isChecked():
            image_path = "{}/{}.{}".format(os.path.dirname(file_path),
                                           os.path.basename(file_path),
                                           self.image_format_names[self.current_image_format])
            qDebug("saving image in:   {}".format(image_path))

            with open(image_path, 'wb') as f:
                f.write(self.cached_image)

        self.editor.document().setModified(False)
        self.setWindowModified(False)
        return True

    def undo(self):
        document = self.editor.document()
        document.undo()
        self.enable_undo_redo_actions()

    def redo(self):
        document = self.editor.document()
        document.redo()
        self.enable_undo_redo_actions()

    def copy_image(self):
        pixmap = QPixmap()
        pixmap.loadFromData(self.cached_image)
        QApplication.clipboard().setPixmap(pixmap)
        qDebug("Image copy into Clipboard")

    def export_image(self, name):
        if self.cached_image is None:
            qDebug("no image to export. aborting...")
            return

        if self.document_path is None:
            qDebug("no image to export. aborting...")
            return

        doc_path_with_base_filename = os.path.join(
            os.path.abspath(self.document_path),
            os.path.basename(self.document_path))
        doc_path_with_base_filename, _ = os.path.splitext(doc_path_with_base_filename)
        doc_path_with_base_filename += ".{}".format(self.image_format_names[self.current_image_format])

        tmp_name = name
        if tmp_name is None:
            tmp_name = QFileDialog.getSaveFileName(self,
                                                   self.tr("Select where to export the image"),
                                                   doc_path_with_base_filename,
                                                   "Image (*.svg *.png);; All Files (*.*)"
                                                   )
            tmp_name = tmp_name[0]
            if not tmp_name:
                return

        qDebug("exporting image in: {}".format(tmp_name))

        with open(tmp_name, 'wb') as f:
            f.write(self.cached_image)

        self.export_image_action.setText(self.tr(EXPORT_TO_MENU_FORMAT_STRING.format(tmp_name)))

        self.export_path = tmp_name

        short_tmp_name = os.path.basename(tmp_name)
        self.statusBar().showMessage(self.tr("Image exported in {}".format(short_tmp_name)), STATUS_BAR_TIMEOUT)
        self.export_path_label.setText(self.tr(EXPORT_TO_LABEL_FORMAT_STRING.format(short_tmp_name)))
        self.export_path_label.setEnabled(True)

    def about(self):
        QMessageBox.about(self,
                          self.tr("About {}".format(QApplication.applicationName())),
                          "Yo a very long string I am")

    def about_qt(self):
        QMessageBox.aboutQt(self,
                            self.tr("About {}".format(QApplication.applicationName())))

    def on_editor_changed(self):
        qDebug("editor changed")
        if not self.refresh_from_cache():
            self.needs_refresh = True

        self.setWindowModified(True)
        self.enable_undo_redo_actions()

    def on_refresh_action_triggered(self):
        self.needs_refresh = True
        self.refresh(True)

    def on_auto_refresh_action_toggled(self, state):
        pass

    def zoom_in(self, widget):
        pass
