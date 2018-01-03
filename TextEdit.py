from PyQt5.QtWidgets import QPlainTextEdit, QWidget, QApplication
from PyQt5.QtCore import QSize, QRect, qDebug
from PyQt5.QtGui import QPainter, QTextBlock, QTextCursor
from PyQt5.Qt import Qt


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super(LineNumberArea, self).__init__(editor)
        self.text_editor = editor

    # Overrides
    def sizeHint(self):
        return QSize(self.text_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.text_editor.line_number_area_paint_event(event)


class TextEdit(QPlainTextEdit):
    def __init__(self, parent):
        super(TextEdit, self).__init__(parent)

        self._indent_size = 4
        self._indent_with_space = False
        self._auto_indent = True

        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)

        self.update_line_number_area_width(0)

    def set_indent_size(self, indent_size):
        self._indent_size = indent_size

    def indent_size(self):
        return self._indent_size

    def set_indent_with_space(self, indent_with_space):
        self._indent_with_space = indent_with_space

    def indent_with_space(self):
        return self._indent_with_space

    def set_auto_indent(self, auto_indent):
        self._auto_indent = auto_indent

    def auto_indent(self):
        return self._auto_indent

    def line_number_area_paint_event(self, event):

        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), Qt.lightGray)

        block = QTextBlock(self.firstVisibleBlock())
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, top, self.line_number_area.width(),
                                 self.fontMetrics().height(), Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def line_number_area_width(self):
        digits = 1
        maximum = max(1, self.blockCount())
        while maximum >= 10:
            maximum /= 10
            digits += 1

        digits = max(3, digits)

        space = 3 + self.fontMetrics().boundingRect('9').width() * digits

        return space

    # Overrides
    def keyPressEvent(self, key_event):
        key = key_event.key()

        if key == Qt.Key_Enter or key == Qt.Key_Return:
            super(TextEdit, self).keyPressEvent(key_event)

            update_cursor = QTextCursor(self.textCursor())

            # Auto - indent
            if self._auto_indent:
                block = QTextBlock(update_cursor.block().previous())

                data = block.text()
                pos = block.length()

                if pos >= len(data):
                    pos = len(data) - 1

                idx = -1
                for i in range(pos, 0, -1):
                    if data[i] == '\n':
                        idx = i
                        break

                while (idx + 1) < len(data) \
                        and data[idx + 1].isspace() \
                        and data[idx + 1] != '\n' \
                        and data[idx + 1] != '\r':
                    update_cursor.insertText(data[idx + 1])
                    idx += 1

        elif key == Qt.Key_Tab or key == Qt.Key_Backtab:
            modifiers = QApplication.keyboardModifiers()
            indent_line = ""
            if self._indent_with_space:
                indent_line = ' ' * self._indent_size
            else:
                indent_line = '\t'

            current_text_cursor = QTextCursor(self.textCursor())
            selection_start = current_text_cursor.selectionStart()
            selection_end = current_text_cursor.selectionEnd()

            if selection_start == selection_end:
                if not (modifiers & Qt.ShiftModifier):
                    current_text_cursor.insertText(indent_line)
                else:
                    current_text_cursor.setPosition(current_text_cursor.block().position())
                    text = current_text_cursor.block().text()
                    for i in range(0, min(len(indent_line), len(text))):
                        if not text[i].isspace():
                            break

                        current_text_cursor.deleteChar()

            else:
                text_block = QTextBlock(self.document().findBlock(selection_start))

                while text_block.isValid() and text_block.position() <= selection_end:
                    current_text_cursor.setPosition(text_block.position())

                    if not (modifiers & Qt.ShiftModifier):
                        current_text_cursor.insertText(indent_line)
                        selection_end += len(indent_line)
                    else:
                        qDebug("<<<")
                        text = current_text_cursor.block().text()
                        for i in range(0, min(len(indent_line), len(text))):
                            if not text[i].isspace():
                                break

                            current_text_cursor.deleteChar()
                            selection_end -= 1

                    text_block = text_block.next()

        else:
            super(TextEdit, self).keyPressEvent(key_event)

    def paintEvent(self, paint_event):
        # Update tab stops
        indent_line = ' ' * self.indent_size()
        self.setTabStopWidth(self.fontMetrics().width(indent_line))

        super(TextEdit, self).paintEvent(paint_event)

    def resizeEvent(self, resize_event):
        super(TextEdit, self).resizeEvent(resize_event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    # Slots
    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)
