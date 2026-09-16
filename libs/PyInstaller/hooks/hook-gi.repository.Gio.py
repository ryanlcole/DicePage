# 005677.python.hook-gi.repository.Gio.line1.comment -----------------------------------------------------------------------------
# 005678.python.hook-gi.repository.Gio.line2.comment Copyright (c) 2005-2025, PyInstaller Development Team.
# 005679.python.hook-gi.repository.Gio.line3.comment
# 005680.python.hook-gi.repository.Gio.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005681.python.hook-gi.repository.Gio.line5.comment or later) with exception for distributing the bootloader.
# 005682.python.hook-gi.repository.Gio.line6.comment
# 005683.python.hook-gi.repository.Gio.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005684.python.hook-gi.repository.Gio.line8.comment
# 005685.python.hook-gi.repository.Gio.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005686.python.hook-gi.repository.Gio.line10.comment -----------------------------------------------------------------------------

import glob
import os

from PyInstaller import compat
import PyInstaller.log as logging
from PyInstaller.utils.hooks.gi import GiModuleInfo

logger = logging.getLogger(__name__)

module_info = GiModuleInfo('Gio', '2.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()

    # 005687.python.hook-gi.repository.Gio.line25.comment Find Gio modules
    libdir = module_info.get_libdir()
    modules_pattern = None
    gio_libdir = os.path.join(libdir, 'gio', 'modules')
    runtime_path = 'gio_modules'

    lib_ext = '*.so'
    if compat.is_win:
        lib_ext = '*.dll'

    if not os.path.exists(gio_libdir):
        # 005688.python.hook-gi.repository.Gio.line36.comment homebrew/MSYS2 may install the files elsewhere...
        gio_libdir = os.path.join(os.path.commonprefix([compat.base_prefix, gio_libdir]), 'lib', 'gio', 'modules')

    if os.path.exists(gio_libdir):
        modules_pattern = os.path.join(gio_libdir, lib_ext)
    else:
        logger.warning('Could not determine Gio modules path!')

    if modules_pattern:
        for f in glob.glob(modules_pattern):
            binaries.append((f, runtime_path))
        cache_file = os.path.join(gio_libdir, 'giomodule.cache')
        if os.path.isfile(cache_file):
            datas.append((cache_file, runtime_path))
    else:
        # 005689.python.hook-gi.repository.Gio.line51.comment To add a new platform add a new elif above with the proper is_<platform> and proper pattern for finding the
        # 005690.python.hook-gi.repository.Gio.line52.comment Gio modules on your platform.
        logger.warning('Bundling Gio modules is not supported on your platform.')

    # 005691.python.hook-gi.repository.Gio.line55.comment Bundle the mime cache -- might not be needed on Windows
    # 005692.python.hook-gi.repository.Gio.line56.comment -> this is used for content type detection (also used by GdkPixbuf)
    # 005693.python.hook-gi.repository.Gio.line57.comment -> gio/xdgmime/xdgmime.c looks for mime/mime.cache in the users home directory, followed by XDG_DATA_DIRS if
    # 005694.python.hook-gi.repository.Gio.line58.comment specified in the environment, otherwise it searches /usr/local/share/ and /usr/share/
    if not compat.is_win:
        _mime_searchdirs = ['/usr/local/share', '/usr/share']
        if 'XDG_DATA_DIRS' in os.environ:
            _mime_searchdirs.insert(0, os.environ['XDG_DATA_DIRS'])

        for sd in _mime_searchdirs:
            spath = os.path.join(sd, 'mime', 'mime.cache')
            if os.path.exists(spath):
                datas.append((spath, 'share/mime'))
                break
