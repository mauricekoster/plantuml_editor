from PyQt5.QtWidgets import QPlainTextEdit


class TextEdit(QPlainTextEdit):
    def __init__(self, parent):
        super(TextEdit, self).__init__(parent)

