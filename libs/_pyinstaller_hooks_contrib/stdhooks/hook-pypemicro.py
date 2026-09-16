# 016076.python.hook-pypemicro.line1.comment ------------------------------------------------------------------
# 016077.python.hook-pypemicro.line2.comment Copyright (c) 2022 PyInstaller Development Team.
# 016078.python.hook-pypemicro.line3.comment
# 016079.python.hook-pypemicro.line4.comment This file is distributed under the terms of the GNU General Public
# 016080.python.hook-pypemicro.line5.comment License (version 2.0 or later).
# 016081.python.hook-pypemicro.line6.comment
# 016082.python.hook-pypemicro.line7.comment The full license is available in LICENSE, distributed with
# 016083.python.hook-pypemicro.line8.comment this software.
# 016084.python.hook-pypemicro.line9.comment
# 016085.python.hook-pypemicro.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016086.python.hook-pypemicro.line11.comment ------------------------------------------------------------------

# 016087.python.hook-pypemicro.line13.comment Hook for the pypemicro module: https://github.com/nxpmicro/pypemicro

import os
from PyInstaller.utils.hooks import get_package_paths, is_module_satisfies
from PyInstaller.log import logger
from PyInstaller.compat import is_darwin

binaries = list()
if is_module_satisfies('pyinstaller >= 5.0'):
    from PyInstaller import isolated

    @isolated.decorate
    def get_safe_libs():
        from pypemicro import PyPemicro
        libs = PyPemicro.get_pemicro_lib_list()
        return libs

    pkg_base, pkg_dir = get_package_paths("pypemicro")
    for lib in get_safe_libs():
        source_path = lib['path']
        source_name = lib['name']
        dest = os.path.relpath(source_path, pkg_base)
        binaries.append((os.path.join(source_path, source_name), dest))
        if is_darwin:
            libusb = os.path.join(source_path, 'libusb.dylib')
            if os.path.exists(libusb):
                binaries.append((libusb, dest))
            else:
                logger.warning("libusb.dylib was not found for Mac OS, ignored")
else:
    logger.warning("hook-pypemicro requires pyinstaller >= 5.0")
