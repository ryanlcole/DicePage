# 012403.python.hook-cairocffi.line1.comment ------------------------------------------------------------------
# 012404.python.hook-cairocffi.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 012405.python.hook-cairocffi.line3.comment
# 012406.python.hook-cairocffi.line4.comment This file is distributed under the terms of the GNU General Public
# 012407.python.hook-cairocffi.line5.comment License (version 2.0 or later).
# 012408.python.hook-cairocffi.line6.comment
# 012409.python.hook-cairocffi.line7.comment The full license is available in LICENSE, distributed with
# 012410.python.hook-cairocffi.line8.comment this software.
# 012411.python.hook-cairocffi.line9.comment
# 012412.python.hook-cairocffi.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012413.python.hook-cairocffi.line11.comment ------------------------------------------------------------------
import ctypes.util
import os

from PyInstaller.depend.utils import _resolveCtypesImports
from PyInstaller.utils.hooks import collect_data_files, is_module_satisfies, logger

datas = collect_data_files("cairocffi")

binaries = []

# 012414.python.hook-cairocffi.line22.comment NOTE: Update this if cairocffi requires more libraries
libs = ["cairo-2", "cairo", "libcairo-2"]

try:
    lib_basenames = []
    for lib in libs:
        libname = ctypes.util.find_library(lib)
        if libname is not None:
            lib_basenames += [os.path.basename(libname)]

    if lib_basenames:
        resolved_libs = _resolveCtypesImports(lib_basenames)
        for resolved_lib in resolved_libs:
            binaries.append((resolved_lib[1], '.'))
except Exception as e:
    logger.warning("Error while trying to find system-installed Cairo library: %s", e)

if not binaries:
    logger.warning("Cairo library not found - cairocffi will likely fail to work!")

# 012415.python.hook-cairocffi.line42.comment cairocffi 1.6.0 requires cairocffi/constants.py source file, so make sure it is collected.
# 012416.python.hook-cairocffi.line43.comment The module collection mode setting requires PyInstaller >= 5.3.
if is_module_satisfies('cairocffi >= 1.6.0'):
    module_collection_mode = {'cairocffi.constants': 'pyz+py'}
