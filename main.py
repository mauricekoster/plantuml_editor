import sys
import os

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from XDG import get_xdr_data_home, get_xdr_data_dirs

from MainWindow import MainWindow

APPLICATION_NAME = "PlantUML Editor"
ORGANIZATION_NAME = APPLICATION_NAME

if __name__ == '__main__':
    print(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'icons'))
    d = []
    d.extend([os.path.join(d, '.icons') for d in get_xdr_data_home()])
    d.extend([os.path.join(d, 'icons') for d in get_xdr_data_dirs()])
    d.extend([os.path.join(os.path.dirname(os.path.realpath(__file__)), 'icons')])

    QIcon.setThemeSearchPaths(d)
    QIcon.setThemeName('default')

    app = QApplication(sys.argv)
    app.setApplicationName(APPLICATION_NAME)
    app.setOrganizationName(ORGANIZATION_NAME)

    w = MainWindow()
    w.new_document()
    w.show()
    sys.exit(app.exec_())
