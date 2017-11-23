import sys

from PyQt5.QtWidgets import QApplication

from MainWindow import MainWindow

APPLICATION_NAME = "PlantUML Editor"
ORGANIZATION_NAME = APPLICATION_NAME

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName(APPLICATION_NAME)
    app.setOrganizationName(ORGANIZATION_NAME)

    w = MainWindow()
    w.new_document()
    w.show()
    sys.exit(app.exec_())
