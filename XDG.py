import sys
import os
import configparser, codecs

icon_theme_config = None
icons_dirs_list = None

#icon_theme_base_dir = '/usr/share/icons'
icon_theme_base_dir = os.path.join(os.path.expanduser('~'), '.icons')
icon_theme_name = 'gnome'

# https://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html

def get_xdr_data_home():
    dirs = []
    entry = 'XDR_DATA_HOME'
    if entry in os.environ:
        dirs.extend( os.environ[entry].split(':'))

    # Try Windows equivalent
    if 'USERPROFILE' in os.environ:
        dirs.append(os.environ['USERPROFILE'])

    if dirs:
        return dirs
    else:
        return os.path.expanduser('~')


def get_xdr_data_dirs():
    dirs = []
    entry = 'XDR_DATA_DIRS'
    if entry in os.environ:
        dirs.extend( os.environ[entry].split(':'))

    # Try Windows equivalent
    if 'ALLUSERSPROFILE' in os.environ:
        dirs.append(os.environ['ALLUSERSPROFILE'])

    if dirs:
        return dirs
    else:
        return '/usr/local/share/:/usr/share/'.split(':')


icon_cache = {}


def get_icon_theme_name():
    return icon_theme_name


def __get_icon_filename_helper(name, dirs, icons='icons'):
    found = False
    fn = None
    for icon_dir in dirs:
        fn = os.path.join(icon_dir, icons, icon_theme_name, 'index.theme')
        if not os.path.exists(fn):
            continue

        icon_theme_config = configparser.ConfigParser()
        icon_theme_config.read_file(codecs.open(fn, "r", "utf8"))

        sub_dirs = icon_theme_config.get('Icon Theme', 'Directories')
        icons_dirs_list = sub_dirs.split(',')
        icons_dirs_list.reverse()

        for d in icons_dirs_list:
            for ext in ['svg', 'png', 'xpm']:
                fn = os.path.join(icon_dir, icons, icon_theme_name, d, "%s.%s" % (name, ext))
                if os.path.exists(fn):
                    found = True
                    break

            if found:
                break

        if found:
            break

    if found:
        return fn
    else:
        return None


def get_icon_filename(name, custom_icon_path=None):

    if name in icon_cache:
        return icon_cache[name]

    if custom_icon_path:
        if type(custom_icon_path) is list:
            custom_dirs = custom_icon_path
        else:
            custom_dirs = [custom_icon_path]
    else:
        custom_dirs = []

    fn = __get_icon_filename_helper(name, custom_dirs)
    if not fn:
        fn = __get_icon_filename_helper(name, get_xdr_data_home(), '.icons')
    if not fn:
        fn = __get_icon_filename_helper(name, get_xdr_data_dirs(), 'icons')

    if fn:
        fn = fn.replace('/', os.path.sep)
        icon_cache[name] = fn
        return fn
    else:
        return None


if __name__ == '__main__':
    print("get_xdr_data_home", get_xdr_data_home())
    print("get_xdr_data_dirs", get_xdr_data_dirs())

    print("get_icon_filename", get_icon_filename('application-exit'))
