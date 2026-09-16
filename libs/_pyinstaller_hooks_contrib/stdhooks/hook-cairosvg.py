# 012417.python.hook-cairosvg.line1.comment ------------------------------------------------------------------
# 012418.python.hook-cairosvg.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 012419.python.hook-cairosvg.line3.comment
# 012420.python.hook-cairosvg.line4.comment This file is distributed under the terms of the GNU General Public
# 012421.python.hook-cairosvg.line5.comment License (version 2.0 or later).
# 012422.python.hook-cairosvg.line6.comment
# 012423.python.hook-cairosvg.line7.comment The full license is available in LICENSE, distributed with
# 012424.python.hook-cairosvg.line8.comment this software.
# 012425.python.hook-cairosvg.line9.comment
# 012426.python.hook-cairosvg.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012427.python.hook-cairosvg.line11.comment ------------------------------------------------------------------
import ctypes.util
import os

from PyInstaller.depend.utils import _resolveCtypesImports
from PyInstaller.utils.hooks import collect_data_files, logger

datas = collect_data_files("cairosvg")

binaries = []

# 012428.python.hook-cairosvg.line22.comment NOTE: Update this if cairosvg requires more libraries
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
    logger.warning("Cairo library not found - cairosvg will likely fail to work!")
