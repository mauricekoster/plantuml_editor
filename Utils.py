from PyQt5.QtCore import QT_TRANSLATE_NOOP

CACHE_SCALE = 1024 * 1024


def cache_size_to_string(size):
    return QT_TRANSLATE_NOOP("%0.2f Mb") % (size / CACHE_SCALE)

