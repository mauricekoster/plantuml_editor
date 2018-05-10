from PyQt5.QtCore import QObject


class RecentDocuments(QObject):
    def __init__(self, max_documents, parent=None):
        super().__init__(parent)

    def accessing(self, name):
        # TODO accessing
        pass
