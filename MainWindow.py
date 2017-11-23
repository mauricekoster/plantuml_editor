from PyQt5.Qt import Qt
from PyQt5.QtCore import QT_TRANSLATE_NOOP, qDebug
from PyQt5.QtGui import QIcon, QKeySequence, QFontMetrics
from PyQt5.QtWidgets import QMainWindow, QScrollArea, QAction, QDockWidget, qApp, QLabel

from ImageFormat import ImageFormat
from PreviewWindow import PreviewWindow
from TextEdit import TextEdit
from FileCache import FileCache

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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1200, 800)
        self.setWindowTitle(TITLE_FORMAT_STRING.format("", qApp.applicationName()))
        self.setWindowIcon(QIcon.fromTheme('application-exit', QIcon('icons/plantuml.png')))

        self.has_valid_paths = False
        self.process = None
        self.current_image_format = ImageFormat.SvgFormat
        self.needs_refresh = False

        self.image_format_names = {
            ImageFormat.SvgFormat: "svg",
            ImageFormat.PngFormat: "png",
        }

        self.cache = FileCache(0, self)

        self.document_path = None
        self.export_path = None
        self.cached_image = None

        self.image_widget = PreviewWindow(self)

        self.image_widget_scrollarea = QScrollArea()
        self.image_widget_scrollarea.setWidget(self.image_widget);
        self.image_widget_scrollarea.setAlignment(Qt.AlignCenter);
        self.image_widget_scrollarea.setWidgetResizable(True);
        self.setCentralWidget(self.image_widget_scrollarea);

        self.create_dock_windows()
        self.create_actions()
        self.create_menus()
        self.create_tool_bars()
        self.create_status_bar()

        self.setUnifiedTitleAndToolBarOnMac(True)

        self.read_settings()

    def create_dock_windows(self):
        dock = QDockWidget(self.tr("Text Editor"), self)
        self.editor = TextEdit(dock)
        self.editor.document().contentsChanged.connect(self.on_editor_changed)
        dock.setWidget(self.editor)
        dock.setObjectName("text_editor")
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def create_actions(self):
        self.new_document_action = QAction(QIcon.fromTheme("document-new",
                                                           QIcon("icons/page_add.png")),
                                           self.tr("&New document"), self)
        self.new_document_action.setShortcut(QKeySequence.New)
        self.new_document_action.triggered.connect(self.new_document)

        self.quit_action = QAction(QIcon.fromTheme("application-exit",
                                                   QIcon("icons/application_delete.png")),
                                   self.tr("&Quit"), self)
        self.quit_action.setShortcuts(QKeySequence.Quit)
        self.quit_action.setStatusTip(self.tr("Quit the application"))
        self.quit_action.triggered.connect(self.close)

        # Edit menu
        self.undo_action = QAction(QIcon.fromTheme("edit-undo", QIcon('icons/arrow_undo.png')),
                                   self.tr("&Undo"), self)
        self.undo_action.setShortcuts(QKeySequence.Undo)
        self.undo_action.triggered.connect(self.undo)

        self.redo_action = QAction(QIcon.fromTheme("edit-redo", QIcon('icons/arrow_redo.png')),
                                   self.tr("&Redo"), self)
        self.redo_action.setShortcuts(QKeySequence.Redo)
        self.redo_action.triggered.connect(self.redo)

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
        # m_mainToolBar->addSeparator();
        # m_mainToolBar->addAction(m_refreshAction);
        # m_mainToolBar->addSeparator();
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

    def read_settings(self):
        pass

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

    def refresh(self, force=False):
        qDebug("Refreshing")
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
        # TODO
        pass
