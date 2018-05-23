import sys
import os

from PyQt5.QtCore import QSettings, qDebug
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from XDG import get_xdr_data_home, get_xdr_data_dirs

from MainWindow import MainWindow

APPLICATION_NAME = "Diagram Editor"
ORGANIZATION_NAME = "mauricekoster.com"


def resource_path(path):
    if getattr(sys, 'frozen', False):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)

    return os.path.join(basedir, path)


if __name__ == '__main__':
    print(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'icons'))
    d = []
    d.extend([os.path.join(d, '.icons') for d in get_xdr_data_home()])
    d.extend([os.path.join(d, 'icons') for d in get_xdr_data_dirs()])
    d.extend([resource_path('icons')])

    QIcon.setThemeSearchPaths(d)
    QIcon.setThemeName('default')

    app = QApplication(sys.argv)
    app.setApplicationName(APPLICATION_NAME)
    app.setOrganizationName(ORGANIZATION_NAME)

    # QSettings.setDefaultFormat(QSettings.IniFormat)


    w = MainWindow()
    w.new_document()
    w.show()
    sys.exit(app.exec_())
