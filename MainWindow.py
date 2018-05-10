import os
import hashlib

from PyQt5.Qt import Qt
from PyQt5.QtCore import QT_TRANSLATE_NOOP, qDebug, QTimer, QSettings, QProcess
from PyQt5.QtCore import QFileInfo
from PyQt5.QtGui import QIcon, QKeySequence, QFontMetrics
from PyQt5.QtWidgets import QMainWindow, QScrollArea, QAction, QDockWidget, qApp, QLabel

from ImageFormat import ImageFormat
from PreviewWindow import PreviewWindow, Mode
from TextEdit import TextEdit
from FileCache import FileCache, FileCacheItem
import SettingsConstants

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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1200, 800)
        self.setWindowTitle(TITLE_FORMAT_STRING.format("", qApp.applicationName()))
        self.setWindowIcon(QIcon('icons/plantuml.png'))

        self.has_valid_paths = False
        self.process = None
        self.current_image_format = ImageFormat.SvgFormat
        self.needs_refresh = False

        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.refresh)

        self.image_format_names = {
            ImageFormat.SvgFormat: "svg",
            ImageFormat.PngFormat: "png",
        }

        self.use_cache = False
        self.cache = FileCache(0, self)
        self.cached_image = None

        self.document_path = None
        self.export_path = None

        self.last_key = None

        self.editor = TextEdit(self)
        self.editor.document().contentsChanged.connect(self.on_editor_changed)

        self.setCentralWidget(self.editor)

        self.create_dock_windows()
        self.create_actions()
        self.create_menus()
        self.create_tool_bars()
        self.create_status_bar()

        self.setUnifiedTitleAndToolBarOnMac(True)

        self.read_settings()

    def create_dock_windows(self):
        dock = QDockWidget(self.tr("Diagram"), self)
        dock.setMinimumWidth(300)

        self.image_widget = PreviewWindow(dock)

        self.image_widget_scrollarea = QScrollArea()
        self.image_widget_scrollarea.setWidget(self.image_widget)
        self.image_widget_scrollarea.setAlignment(Qt.AlignCenter)
        self.image_widget_scrollarea.setWidgetResizable(True)

        dock.setWidget(self.image_widget_scrollarea)
        dock.setObjectName("diagram")
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def create_actions(self):
        self.new_document_action = QAction(QIcon.fromTheme("document-new"),
                                           self.tr("&New document"), self)
        self.new_document_action.setShortcut(QKeySequence.New)
        self.new_document_action.triggered.connect(self.new_document)

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

        self.auto_refresh_action = QAction()

        # Refresh
        self.refresh_action = QAction(QIcon.fromTheme("view-refresh"), self.tr("Refresh"), self)
        self.refresh_action.setShortcuts(QKeySequence.Refresh)
        self.refresh_action.setStatusTip(self.tr("Call PlantUML to regenerate the UML image"))
        self.refresh_action.triggered.connect(self.on_refresh_action_triggered)

        self.auto_refresh_action = QAction(self.tr("Auto-Refresh"), self)
        self.auto_refresh_action.setCheckable(True)
        self.auto_refresh_action.toggled.connect(self.on_auto_refresh_action_toggled)

        self.auto_save_image_action = QAction(self.tr("Auto-Save image"), self)
        self.auto_save_image_action.setCheckable(True)


    def create_menus(self):
        self.file_menu = self.menuBar().addMenu(self.tr("&File"))
        self.file_menu.addAction(self.new_document_action)
        # m_fileMenu->addAction(m_openDocumentAction);
        # m_fileMenu->addAction(m_saveDocumentAction);
        # m_fileMenu->addAction(m_saveAsDocumentAction);
        # m_fileMenu->addSeparator();
        # QMenu * recent_documents_submenu = m_fileMenu->addMenu(tr("Recent Documents"));
        # recent_documents_submenu->addActions(m_recentDocuments->actions());
        # m_fileMenu->addSeparator();
        # m_fileMenu->addAction(m_exportImageAction);
        # m_fileMenu->addAction(m_exportAsImageAction);
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.quit_action)

        self.edit_menu = self.menuBar().addMenu(self.tr("&Edit"))
        self.edit_menu.addAction(self.undo_action)
        self.edit_menu.addAction(self.redo_action)
        # self.edit_menu.addAction(m_copyImageAction)
        self.edit_menu.addSeparator()
        # self.edit_menu.addAction(m_refreshAction)

    def create_tool_bars(self):
        self.main_tool_bar = self.addToolBar(self.tr("MainToolbar"))
        self.main_tool_bar.setObjectName("main_toolbar")
        # self.main_tool_bar.addAction(self.quit_action)
        self.main_tool_bar.addAction(self.new_document_action)
        # m_mainToolBar->addAction(m_openDocumentAction);
        # m_mainToolBar->addAction(m_saveDocumentAction);
        # m_mainToolBar->addAction(m_saveAsDocumentAction);
        # m_mainToolBar->addSeparator();
        # m_mainToolBar->addAction(m_showAssistantDockAction);
        # m_mainToolBar->addAction(m_showAssistantInfoDockAction);
        # m_mainToolBar->addAction(m_showEditorDockAction);
        self.main_tool_bar.addSeparator()
        self.main_tool_bar.addAction(self.undo_action)
        self.main_tool_bar.addAction(self.redo_action)
        self.main_tool_bar.addSeparator()
        self.main_tool_bar.addAction(self.refresh_action)
        # self.main_tool_bar->addSeparator();
        # m_mainToolBar->addAction(m_preferencesAction);
        #
        # m_zoomToolBar = addToolBar(tr("ZoomToolbar"));
        # m_zoomToolBar->setObjectName("zoom_toolbar");
        # addZoomActions(m_zoomToolBar);

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
        self.has_valid_paths = True

    def read_settings(self, reload=False):
        settings = QSettings()

        # m_useCustomJava = settings.value(SETTINGS_USE_CUSTOM_JAVA, SETTINGS_USE_CUSTOM_JAVA_DEFAULT).toBool();
        # m_customJavaPath = settings.value(SETTINGS_CUSTOM_JAVA_PATH, SETTINGS_CUSTOM_JAVA_PATH_DEFAULT).toString();
        # m_javaPath = m_useCustomJava ? m_customJavaPath: SETTINGS_CUSTOM_JAVA_PATH_DEFAULT;
        #
        # m_useCustomPlantUml = settings.value(SETTINGS_USE_CUSTOM_PLANTUML,
        #                                      SETTINGS_USE_CUSTOM_PLANTUML_DEFAULT).toBool();
        # m_customPlantUmlPath = settings.value(SETTINGS_CUSTOM_PLANTUML_PATH,
        #                                       SETTINGS_CUSTOM_PLANTUML_PATH_DEFAULT).toString();
        # m_plantUmlPath = m_useCustomPlantUml ? m_customPlantUmlPath: SETTINGS_CUSTOM_PLANTUML_PATH_DEFAULT;

        self.java_path = 'C:/Program Files/Java/jre1.8.0_171/bin/java.exe'
        self.plantuml_path = 'e:/Tools/plantuml.1.2017.19.jar'
        self.graphviz_path = 'C:/Program Files (x86)/Graphviz2.38/'
        self.check_paths()

        value = self.image_format_names[ImageFormat.PngFormat]
        # value = settings.value(SettingsConstants.SETTINGS_IMAGE_FORMAT,
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

        self.autorefresh_enabled = settings.value(SettingsConstants.SETTINGS_AUTOREFRESH_ENABLED, 'true') == 'true'
        self.auto_refresh_action.setChecked(self.autorefresh_enabled)
        self.auto_refresh_timer.setInterval(
            settings.value(SettingsConstants.SETTINGS_AUTOREFRESH_TIMEOUT,
                           int(SettingsConstants.SETTINGS_AUTOREFRESH_TIMEOUT_DEFAULT)))

        if self.autorefresh_enabled:
            qDebug("starting auto refresh timer")
            self.auto_refresh_timer.start()

        self.auto_refresh_label.setEnabled(self.autorefresh_enabled)

    def maybe_save(self):
        # TODO
        return True

    def new_document(self):
        if not self.maybe_save():
            return

        self.document_path = None
        self.export_path = None
        self.cached_image = None

        text = "@startuml\n\nclass Foo\n\n@enduml"
        self.editor.setPlainText(text)
        self.setWindowTitle(TITLE_FORMAT_STRING.format(
            self.tr("Untitled"),
            qApp.applicationName()))

        self.setWindowModified(False)
        self.refresh()

        self.enable_undo_redo_actions()

    def make_key_for_document(self, current_document):
        key = "%s.%s" % (compute_md5_hash(current_document),
                         self.image_format_names[self.current_image_format])

        return key

    def refresh_from_cache(self):
        # TODO
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

    def undo(self):
        # TODO: undo
        pass

    def redo(self):
        # TODO: redo
        pass

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