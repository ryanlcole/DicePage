# 017189.python.hook-soundfile.line1.comment ------------------------------------------------------------------
# 017190.python.hook-soundfile.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 017191.python.hook-soundfile.line3.comment
# 017192.python.hook-soundfile.line4.comment This file is distributed under the terms of the GNU General Public
# 017193.python.hook-soundfile.line5.comment License (version 2.0 or later).
# 017194.python.hook-soundfile.line6.comment
# 017195.python.hook-soundfile.line7.comment The full license is available in LICENSE, distributed with
# 017196.python.hook-soundfile.line8.comment this software.
# 017197.python.hook-soundfile.line9.comment
# 017198.python.hook-soundfile.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017199.python.hook-soundfile.line11.comment ------------------------------------------------------------------
"""
pysoundfile:
https://github.com/bastibe/SoundFile
"""

import pathlib

from PyInstaller.utils.hooks import get_module_file_attribute, logger

binaries = []
datas = []

# 017200.python.hook-soundfile.line24.comment PyPI wheels for Windows and macOS ship the sndfile shared library in _soundfile_data directory,
# 017201.python.hook-soundfile.line25.comment located next to the soundfile.py module file (i.e., in the site-packages directory).
module_dir = pathlib.Path(get_module_file_attribute('soundfile')).parent
data_dir = module_dir / '_soundfile_data'
if data_dir.is_dir():
    destdir = str(data_dir.relative_to(module_dir))

    # 017202.python.hook-soundfile.line31.comment Collect the shared library (known variants: libsndfile64bit.dll, libsndfile32bit.dll, libsndfile.dylib)
    for lib_file in data_dir.glob("libsndfile*.*"):
        binaries += [(str(lib_file), destdir)]

    # 017203.python.hook-soundfile.line35.comment Collect the COPYING file
    copying_file = data_dir / "COPYING"
    if copying_file.is_file():
        datas += [(str(copying_file), destdir)]
else:
    # 017204.python.hook-soundfile.line40.comment On linux and in Anaconda in all OSes, the system-installed sndfile library needs to be collected.
    def _find_system_sndfile_library():
        import os
        import ctypes.util
        from PyInstaller.depend.utils import _resolveCtypesImports

        libname = ctypes.util.find_library("sndfile")
        if libname is not None:
            resolved_binary = _resolveCtypesImports([os.path.basename(libname)])
            if resolved_binary:
                return resolved_binary[0][1]

    try:
        lib_file = _find_system_sndfile_library()
    except Exception as e:
        logger.warning("Error while trying to find system-installed sndfile library: %s", e)
        lib_file = None

    if lib_file:
        binaries += [(lib_file, '.')]

if not binaries:
    logger.warning("sndfile shared library not found - soundfile will likely fail to work!")
