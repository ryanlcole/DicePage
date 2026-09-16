# 020018.python.hook-weasyprint.line1.comment ------------------------------------------------------------------
# 020019.python.hook-weasyprint.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 020020.python.hook-weasyprint.line3.comment
# 020021.python.hook-weasyprint.line4.comment This file is distributed under the terms of the GNU General Public
# 020022.python.hook-weasyprint.line5.comment License (version 2.0 or later).
# 020023.python.hook-weasyprint.line6.comment
# 020024.python.hook-weasyprint.line7.comment The full license is available in LICENSE, distributed with
# 020025.python.hook-weasyprint.line8.comment this software.
# 020026.python.hook-weasyprint.line9.comment
# 020027.python.hook-weasyprint.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 020028.python.hook-weasyprint.line11.comment ------------------------------------------------------------------

# 020029.python.hook-weasyprint.line13.comment Hook for weasyprint: https://pypi.python.org/pypi/WeasyPrint
# 020030.python.hook-weasyprint.line14.comment Tested on version weasyprint 54.0 using Windows 10 and python 3.8
# 020031.python.hook-weasyprint.line15.comment Note that weasyprint < 54.0 does not work on python 3.8 due to https://github.com/Kozea/WeasyPrint/issues/1435
# 020032.python.hook-weasyprint.line16.comment For weasyprint < 53.0 the required libs are
# 020033.python.hook-weasyprint.line17.comment libs = [
# 020034.python.hook-weasyprint.line18.comment 'gobject-2.0', 'libgobject-2.0-0', 'libgobject-2.0.so.0', 'libgobject-2.0.dylib',
# 020035.python.hook-weasyprint.line19.comment 'pango-1.0', 'libpango-1.0-0', 'libpango-1.0.so.0', 'libpango-1.0.dylib',
# 020036.python.hook-weasyprint.line20.comment 'pangocairo-1.0', 'libpangocairo-1.0-0', 'libpangocairo-1.0.so.0', 'libpangocairo-1.0.dylib',
# 020037.python.hook-weasyprint.line21.comment 'fontconfig', 'libfontconfig', 'libfontconfig-1.dll', 'libfontconfig.so.1', 'libfontconfig-1.dylib',
# 020038.python.hook-weasyprint.line22.comment 'pangoft2-1.0', 'libpangoft2-1.0-0', 'libpangoft2-1.0.so.0', 'libpangoft2-1.0.dylib'
# 020039.python.hook-weasyprint.line23.comment ]

import ctypes.util
import os
from pathlib import Path

from PyInstaller.compat import is_win
from PyInstaller.depend.utils import _resolveCtypesImports
from PyInstaller.utils.hooks import collect_data_files, logger

datas = collect_data_files('weasyprint')
binaries = []
fontconfig_config_dir_found = False

# 020040.python.hook-weasyprint.line37.comment On Windows, a GTK3-installation provides fontconfig and the corresponding fontconfig conf files. We have to add these
# 020041.python.hook-weasyprint.line38.comment for weasyprint to correctly use fonts.
# 020042.python.hook-weasyprint.line39.comment NOTE: Update these lists if weasyprint requires more libraries
fontconfig_libs = [
    'fontconfig-1', 'fontconfig', 'libfontconfig', 'libfontconfig-1.dll', 'libfontconfig.so.1', 'libfontconfig-1.dylib'
]
libs = [
    'gobject-2.0-0', 'gobject-2.0', 'libgobject-2.0-0', 'libgobject-2.0.so.0', 'libgobject-2.0.dylib',
    'pango-1.0-0', 'pango-1.0', 'libpango-1.0-0', 'libpango-1.0.so.0', 'libpango-1.0.dylib',
    'harfbuzz', 'harfbuzz-0.0', 'libharfbuzz-0', 'libharfbuzz.so.0', 'libharfbuzz.so.0', 'libharfbuzz.0.dylib',
    'pangoft2-1.0-0', 'pangoft2-1.0', 'libpangoft2-1.0-0', 'libpangoft2-1.0.so.0', 'libpangoft2-1.0.dylib'
]

try:
    lib_basenames = []
    for lib in libs:
        libname = ctypes.util.find_library(lib)
        if libname is not None:
            lib_basenames += [os.path.basename(libname)]
    for lib in fontconfig_libs:
        libname = ctypes.util.find_library(lib)
        if libname is not None:
            lib_basenames += [os.path.basename(libname)]
            # 020043.python.hook-weasyprint.line60.comment Try to load fontconfig config files on Windows from a GTK-installation
            if is_win:
                fontconfig_config_dir = Path(libname).parent.parent / 'etc/fonts'
                if fontconfig_config_dir.exists() and fontconfig_config_dir.is_dir():
                    datas += [(str(fontconfig_config_dir), 'etc/fonts')]
                    fontconfig_config_dir_found = True
    if lib_basenames:
        resolved_libs = _resolveCtypesImports(lib_basenames)
        for resolved_lib in resolved_libs:
            binaries.append((resolved_lib[1], '.'))
    # 020044.python.hook-weasyprint.line70.comment Try to load fontconfig config files on other OS
    fontconfig_config_dir = Path('/etc/fonts')
    if fontconfig_config_dir.exists() and fontconfig_config_dir.is_dir():
        datas += [(str(fontconfig_config_dir), 'etc/fonts')]
        fontconfig_config_dir_found = True

except Exception as e:
    logger.warning('Error while trying to find system-installed depending libraries: %s', e)

if not binaries:
    logger.warning('Depending libraries not found - weasyprint will likely fail to work!')

if not fontconfig_config_dir_found:
    logger.warning(
        'Fontconfig configuration files not found - weasyprint will likely throw warnings and use default fonts!'
    )
