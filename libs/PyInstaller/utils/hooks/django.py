# 009988.python.django.line1.comment ----------------------------------------------------------------------------
# 009989.python.django.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 009990.python.django.line3.comment
# 009991.python.django.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 009992.python.django.line5.comment or later) with exception for distributing the bootloader.
# 009993.python.django.line6.comment
# 009994.python.django.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 009995.python.django.line8.comment
# 009996.python.django.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 009997.python.django.line10.comment ----------------------------------------------------------------------------
import os

from PyInstaller import isolated


@isolated.decorate
def django_dottedstring_imports(django_root_dir):
    """
    An isolated helper that returns list of all Django dependencies, parsed from the `mysite.settings` module.

    NOTE: With newer version of Django this is most likely the part of PyInstaller that will be broken.

    Tested with Django 2.2
    """

    import sys
    import os

    import PyInstaller.utils.misc
    from PyInstaller.utils import hooks as hookutils

    # 009998.python.django.line32.comment Extra search paths to add to sys.path:
    # 009999.python.django.line33.comment - parent directory of the django_root_dir
    # 010000.python.django.line34.comment - django_root_dir itself; often, Django users do not specify absolute imports in the settings module.
    search_paths = [
        PyInstaller.utils.misc.get_path_to_toplevel_modules(django_root_dir),
        django_root_dir,
    ]
    sys.path += search_paths

    # 010001.python.django.line41.comment Set the path to project's settings module
    default_settings_module = os.path.basename(django_root_dir) + '.settings'
    settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', default_settings_module)
    os.environ['DJANGO_SETTINGS_MODULE'] = settings_module

    # 010002.python.django.line46.comment Calling django.setup() avoids the exception AppRegistryNotReady() and also reads the user settings
    # 010003.python.django.line47.comment from DJANGO_SETTINGS_MODULE.
    # 010004.python.django.line48.comment https://stackoverflow.com/questions/24793351/django-appregistrynotready
    import django  # noqa: E402

    django.setup()

    # 010006.python.django.line53.comment This allows to access all django settings even from the settings.py module.
    from django.conf import settings  # noqa: E402

    hiddenimports = list(settings.INSTALLED_APPS)

    # 010008.python.django.line58.comment Do not fail script when settings does not have such attributes.
    if hasattr(settings, 'TEMPLATE_CONTEXT_PROCESSORS'):
        hiddenimports += list(settings.TEMPLATE_CONTEXT_PROCESSORS)

    if hasattr(settings, 'TEMPLATE_LOADERS'):
        hiddenimports += list(settings.TEMPLATE_LOADERS)

    hiddenimports += [settings.ROOT_URLCONF]

    def _remove_class(class_name):
        return '.'.join(class_name.split('.')[0:-1])

    # 010009.python.django.line70.comment -- Changes in Django 1.7.

    # 010010.python.django.line72.comment Remove class names and keep just modules.
    if hasattr(settings, 'AUTHENTICATION_BACKENDS'):
        for cl in settings.AUTHENTICATION_BACKENDS:
            cl = _remove_class(cl)
            hiddenimports.append(cl)
    # 010011.python.django.line77.comment Deprecated since 4.2, may be None until it is removed
    cl = getattr(settings, 'DEFAULT_FILE_STORAGE', None)
    if cl:
        hiddenimports.append(_remove_class(cl))
    if hasattr(settings, 'FILE_UPLOAD_HANDLERS'):
        for cl in settings.FILE_UPLOAD_HANDLERS:
            cl = _remove_class(cl)
            hiddenimports.append(cl)
    if hasattr(settings, 'MIDDLEWARE_CLASSES'):
        for cl in settings.MIDDLEWARE_CLASSES:
            cl = _remove_class(cl)
            hiddenimports.append(cl)
    # 010012.python.django.line89.comment Templates is a dict:
    if hasattr(settings, 'TEMPLATES'):
        for templ in settings.TEMPLATES:
            backend = _remove_class(templ['BACKEND'])
            hiddenimports.append(backend)
            # 010013.python.django.line94.comment Include context_processors.
            if hasattr(templ, 'OPTIONS'):
                if hasattr(templ['OPTIONS'], 'context_processors'):
                    # 010014.python.django.line97.comment Context processors are functions - strip last word.
                    mods = templ['OPTIONS']['context_processors']
                    mods = [_remove_class(x) for x in mods]
                    hiddenimports += mods
    # 010015.python.django.line101.comment Include database backends - it is a dict.
    for v in settings.DATABASES.values():
        hiddenimports.append(v['ENGINE'])

    # 010016.python.django.line105.comment Add templatetags and context processors for each installed app.
    for app in settings.INSTALLED_APPS:
        app_templatetag_module = app + '.templatetags'
        app_ctx_proc_module = app + '.context_processors'
        hiddenimports.append(app_templatetag_module)
        hiddenimports += hookutils.collect_submodules(app_templatetag_module)
        hiddenimports.append(app_ctx_proc_module)

    # 010017.python.django.line113.comment Deduplicate imports.
    hiddenimports = list(set(hiddenimports))

    # 010018.python.django.line116.comment Return the hidden imports
    return hiddenimports


def django_find_root_dir():
    """
    Return path to directory (top-level Python package) that contains main django files. Return None if no directory
    was detected.

    Main Django project directory contain files like '__init__.py', 'settings.py' and 'url.py'.

    In Django 1.4+ the script 'manage.py' is not in the directory with 'settings.py' but usually one level up. We
    need to detect this special case too.
    """
    # 010019.python.django.line130.comment 'PyInstaller.config' cannot be imported as other top-level modules.
    from PyInstaller.config import CONF

    # 010020.python.django.line133.comment Get the directory with manage.py. Manage.py is supplied to PyInstaller as the first main executable script.
    manage_py = CONF['main_script']
    manage_dir = os.path.dirname(os.path.abspath(manage_py))

    # 010021.python.django.line137.comment Get the Django root directory. The directory that contains settings.py and url.py. It could be the directory
    # 010022.python.django.line138.comment containing manage.py or any of its subdirectories.
    settings_dir = None
    files = set(os.listdir(manage_dir))
    if ('settings.py' in files or 'settings' in files) and 'urls.py' in files:
        settings_dir = manage_dir
    else:
        for f in files:
            if os.path.isdir(os.path.join(manage_dir, f)):
                subfiles = os.listdir(os.path.join(manage_dir, f))
                # 010023.python.django.line147.comment Subdirectory contains critical files.
                if ('settings.py' in subfiles or 'settings' in subfiles) and 'urls.py' in subfiles:
                    settings_dir = os.path.join(manage_dir, f)
                    break  # Find the first directory.

    return settings_dir
