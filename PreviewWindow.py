from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QImage, QPainter
from PySide6.QtCore import QSize, QRect, QPoint, Qt
from PySide6.QtSvg import QSvgRenderer

ZOOM_ORIGINAL_SCALE = 100
ZOOM_BIG_INCREMENT = 100  # used when m_zoomScale > ZOOM_ORIGINAL_SCALE
ZOOM_SMALL_INCREMENT = 20  # used when m_zoomScale < ZOOM_ORIGINAL_SCALE
MAX_ZOOM_SCALE = 900
MIN_ZOOM_SCALE = 10


class Mode:
    NoMode = 0
    PngMode = 1
    SvgMode = 2


class PreviewWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mode = Mode.NoMode
        self.image = QImage()
        self.zoomed_image = QImage()
        self.svgRenderer = QSvgRenderer(self)
        self.zoom_scale = ZOOM_ORIGINAL_SCALE

    def mode(self):
        return self.mode

    def set_mode(self, mode):
        self.mode = mode

    def load(self, data):
        if self.mode == Mode.PngMode:
            self.image.loadFromData(data)
            self.setMinimumSize(self.image.rect().size())
        elif self.mode == Mode.SvgMode:
            self.svgRenderer.load(data)

        self.zoom_image()
        self.update()

    # Public slots
    def zoom_original(self):
        self.set_zoom_scale(ZOOM_ORIGINAL_SCALE)

    def zoom_in(self):
        # new_scale = self.zoom_scale + \
        #             ZOOM_BIG_INCREMENT if self.zoom_scale >= ZOOM_ORIGINAL_SCALE else ZOOM_SMALL_INCREMENT
        new_scale = self.zoom_scale + ZOOM_SMALL_INCREMENT
        if new_scale > MAX_ZOOM_SCALE:
            new_scale = MAX_ZOOM_SCALE
        self.set_zoom_scale(new_scale)

    def zoom_out(self):
        # new_scale = self.zoom_scale - \
        #             ZOOM_SMALL_INCREMENT if self.zoom_scale <= ZOOM_ORIGINAL_SCALE else ZOOM_BIG_INCREMENT
        new_scale = self.zoom_scale - ZOOM_SMALL_INCREMENT
        if new_scale < MIN_ZOOM_SCALE:
            new_scale = MIN_ZOOM_SCALE
        self.set_zoom_scale(new_scale)

    # Private methods

    def paintEvent(self, event):
        painter = QPainter(self)
        output_size = QSize()

        if self.mode == Mode.PngMode:
            output_size = self.zoomed_image.size()
            output_rect = QRect(QPoint(), output_size)
            output_rect.translate(self.rect().center() - output_rect.center())
            painter.drawImage(output_rect.topLeft(), self.zoomed_image)

        elif self.mode == Mode.SvgMode:
            output_size = self.svgRenderer.defaultSize()
            if self.zoom_scale != ZOOM_ORIGINAL_SCALE:
                zoom = float(self.zoom_scale) / ZOOM_ORIGINAL_SCALE
                output_size.scale(output_size.width() * zoom, output_size.height() * zoom, Qt.IgnoreAspectRatio)

            output_rect = QRect(QPoint(), output_size)
            output_rect.translate(self.rect().center() - output_rect.center())
            self.svgRenderer.render(painter, output_rect)

        self.setMinimumSize(output_size)

    def zoom_image(self):
        if self.mode == Mode.PngMode:
            if self.zoom_scale == ZOOM_ORIGINAL_SCALE:
                self.zoomed_image = self.image
            else:
                zoom = float(self.zoom_scale) / ZOOM_ORIGINAL_SCALE
                self.zoomed_image = self.image.scaled(self.image.width() * zoom, self.image.height() * zoom,
                                                      Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

    def set_zoom_scale(self, new_scale):
        if self.zoom_scale != new_scale:
            self.zoom_scale = new_scale
            self.zoom_image()
            self.update()
