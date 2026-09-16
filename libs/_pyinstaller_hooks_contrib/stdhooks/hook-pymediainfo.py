# 015964.python.hook-pymediainfo.line1.comment ------------------------------------------------------------------
# 015965.python.hook-pymediainfo.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 015966.python.hook-pymediainfo.line3.comment
# 015967.python.hook-pymediainfo.line4.comment This file is distributed under the terms of the GNU General Public
# 015968.python.hook-pymediainfo.line5.comment License (version 2.0 or later).
# 015969.python.hook-pymediainfo.line6.comment
# 015970.python.hook-pymediainfo.line7.comment The full license is available in LICENSE, distributed with
# 015971.python.hook-pymediainfo.line8.comment this software.
# 015972.python.hook-pymediainfo.line9.comment
# 015973.python.hook-pymediainfo.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015974.python.hook-pymediainfo.line11.comment ------------------------------------------------------------------

from PyInstaller.compat import is_win, is_darwin
from PyInstaller.utils.hooks import collect_dynamic_libs, logger

# 015975.python.hook-pymediainfo.line16.comment Collect bundled mediainfo shared library (available in Windows and macOS wheels on PyPI).
binaries = collect_dynamic_libs("pymediainfo")

# 015976.python.hook-pymediainfo.line19.comment On linux, no wheels are available, and pymediainfo uses system shared library.
if not binaries and not (is_win or is_darwin):

    def _find_system_mediainfo_library():
        import os
        import ctypes.util
        from PyInstaller.depend.utils import _resolveCtypesImports

        libname = ctypes.util.find_library("mediainfo")
        if libname is not None:
            resolved_binary = _resolveCtypesImports([os.path.basename(libname)])
            if resolved_binary:
                return resolved_binary[0][1]

    try:
        mediainfo_lib = _find_system_mediainfo_library()
    except Exception as e:
        logger.warning("Error while trying to find system-installed MediaInfo library: %s", e)
        mediainfo_lib = None

    if mediainfo_lib:
        # 015977.python.hook-pymediainfo.line40.comment Put the library into pymediainfo sub-directory, to keep layout consistent with that of wheels.
        binaries += [(mediainfo_lib, 'pymediainfo')]

if not binaries:
    logger.warning("MediaInfo shared library not found - pymediainfo will likely fail to work!")
