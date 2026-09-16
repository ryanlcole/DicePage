# 005437.python.hook-django.line1.comment -----------------------------------------------------------------------------
# 005438.python.hook-django.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005439.python.hook-django.line3.comment
# 005440.python.hook-django.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005441.python.hook-django.line5.comment or later) with exception for distributing the bootloader.
# 005442.python.hook-django.line6.comment
# 005443.python.hook-django.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005444.python.hook-django.line8.comment
# 005445.python.hook-django.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005446.python.hook-django.line10.comment -----------------------------------------------------------------------------

# 005447.python.hook-django.line12.comment Tested with django 2.2

import glob
import os

from PyInstaller import log as logging
from PyInstaller.utils import hooks
from PyInstaller.utils.hooks import django

logger = logging.getLogger(__name__)

# 005448.python.hook-django.line23.comment Collect everything. Some submodules of django are not importable without considerable external setup. Ignore the
# 005449.python.hook-django.line24.comment errors they raise.
datas, binaries, hiddenimports = hooks.collect_all('django', on_error="ignore")

root_dir = django.django_find_root_dir()
if root_dir:
    logger.info('Django root directory %s', root_dir)
    # 005450.python.hook-django.line30.comment Include imports from the mysite.settings.py module.
    settings_py_imports = django.django_dottedstring_imports(root_dir)
    # 005451.python.hook-django.line32.comment Include all submodules of all imports detected in mysite.settings.py.
    for submod in settings_py_imports:
        hiddenimports.append(submod)
        hiddenimports += hooks.collect_submodules(submod)
    # 005452.python.hook-django.line36.comment Include main django modules - settings.py, urls.py, wsgi.py. Without them the django server won't run.
    package_name = os.path.basename(root_dir)
    default_settings_module = f'{package_name}.settings'
    settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', default_settings_module)
    hiddenimports += [
        # 005453.python.hook-django.line41.comment TODO: consider including 'mysite.settings.py' in source code as a data files,
        # 005454.python.hook-django.line42.comment since users might need to edit this file.
        settings_module,
        package_name + '.urls',
        package_name + '.wsgi',
    ]
    # 005455.python.hook-django.line47.comment Django hiddenimports from the standard Python library.
    hiddenimports += [
        'http.cookies',
        'html.parser',
    ]

    # 005456.python.hook-django.line53.comment Bundle django DB schema migration scripts as data files. They are necessary for some commands.
    logger.info('Collecting Django migration scripts.')
    migration_modules = [
        'django.conf.app_template.migrations',
        'django.contrib.admin.migrations',
        'django.contrib.auth.migrations',
        'django.contrib.contenttypes.migrations',
        'django.contrib.flatpages.migrations',
        'django.contrib.redirects.migrations',
        'django.contrib.sessions.migrations',
        'django.contrib.sites.migrations',
    ]
    # 005457.python.hook-django.line65.comment Include migration scripts of Django-based apps too.
    installed_apps = hooks.get_module_attribute(settings_module, 'INSTALLED_APPS')
    migration_modules.extend(set(app + '.migrations' for app in installed_apps))
    # 005458.python.hook-django.line68.comment Copy migration files.
    for mod in migration_modules:
        mod_name, bundle_name = mod.split('.', 1)
        mod_dir = os.path.dirname(hooks.get_module_file_attribute(mod_name))
        bundle_dir = bundle_name.replace('.', os.sep)
        pattern = os.path.join(mod_dir, bundle_dir, '*.py')
        files = glob.glob(pattern)
        for f in files:
            datas.append((f, os.path.join(mod_name, bundle_dir)))

    # 005459.python.hook-django.line78.comment Include data files from your Django project found in your django root package.
    datas += hooks.collect_data_files(package_name)

    # 005460.python.hook-django.line81.comment Include database file if using sqlite. The sqlite database is usually next to the manage.py script.
    root_dir_parent = os.path.dirname(root_dir)
    # 005461.python.hook-django.line83.comment TODO Add more patterns if necessary.
    _patterns = ['*.db', 'db.*']
    for p in _patterns:
        files = glob.glob(os.path.join(root_dir_parent, p))
        for f in files:
            # 005462.python.hook-django.line88.comment Place those files next to the executable.
            datas.append((f, '.'))

else:
    logger.warning('No django root directory could be found!')
