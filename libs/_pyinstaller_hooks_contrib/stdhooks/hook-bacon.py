# 012208.python.hook-bacon.line1.comment ------------------------------------------------------------------
# 012209.python.hook-bacon.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012210.python.hook-bacon.line3.comment
# 012211.python.hook-bacon.line4.comment This file is distributed under the terms of the GNU General Public
# 012212.python.hook-bacon.line5.comment License (version 2.0 or later).
# 012213.python.hook-bacon.line6.comment
# 012214.python.hook-bacon.line7.comment The full license is available in LICENSE, distributed with
# 012215.python.hook-bacon.line8.comment this software.
# 012216.python.hook-bacon.line9.comment
# 012217.python.hook-bacon.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012218.python.hook-bacon.line11.comment ------------------------------------------------------------------

# 012219.python.hook-bacon.line13.comment Hook for Bacon (https://github.com/aholkner/bacon)
# 012220.python.hook-bacon.line14.comment Bacon requires its native DLLs to be copied alongside frozen executable.

import os
import ctypes

from PyInstaller.compat import is_win, is_darwin
from PyInstaller.utils.hooks import get_package_paths


def collect_native_files(package, files):
    pkg_base, pkg_dir = get_package_paths(package)
    return [(os.path.join(pkg_dir, file), '.') for file in files]


if is_win:
    files = ['Bacon.dll',
             'd3dcompiler_46.dll',
             'libEGL.dll',
             'libGLESv2.dll',
             'msvcp110.dll',
             'msvcr110.dll',
             'vccorllib110.dll']
    if ctypes.sizeof(ctypes.c_void_p) == 4:
        hiddenimports = ["bacon.windows32"]
        datas = collect_native_files('bacon.windows32', files)
    else:
        hiddenimports = ["bacon.windows64"]
        datas = collect_native_files('bacon.windows64', files)
elif is_darwin:
    if ctypes.sizeof(ctypes.c_void_p) == 4:
        hiddenimports = ["bacon.darwin32"]
        files = ['Bacon.dylib']
        datas = collect_native_files('bacon.darwin32', files)
    else:
        hiddenimports = ["bacon.darwin64"]
        files = ['Bacon64.dylib']
        datas = collect_native_files('bacon.darwin64', files)
