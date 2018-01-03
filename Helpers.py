import os
from PyQt5.QtGui import QIcon
from XDG import get_icon_filename


def get_qicon_from_theme_name(name):
    fn = get_icon_filename(name)
    if fn:
        return QIcon(fn)

    for ext in ['svg', 'png']:
        fn = os.path.join('icons', '%s.%s' % (name, ext))
        if os.path.exists(fn):
            return QIcon(fn)

    return None
