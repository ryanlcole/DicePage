# 017173.python.hook-sounddevice.line1.comment ------------------------------------------------------------------
# 017174.python.hook-sounddevice.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 017175.python.hook-sounddevice.line3.comment
# 017176.python.hook-sounddevice.line4.comment This file is distributed under the terms of the GNU General Public
# 017177.python.hook-sounddevice.line5.comment License (version 2.0 or later).
# 017178.python.hook-sounddevice.line6.comment
# 017179.python.hook-sounddevice.line7.comment The full license is available in LICENSE, distributed with
# 017180.python.hook-sounddevice.line8.comment this software.
# 017181.python.hook-sounddevice.line9.comment
# 017182.python.hook-sounddevice.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017183.python.hook-sounddevice.line11.comment ------------------------------------------------------------------
"""
sounddevice:
https://github.com/spatialaudio/python-sounddevice/
"""

import pathlib

from PyInstaller.utils.hooks import get_module_file_attribute, logger

binaries = []
datas = []

# 017184.python.hook-sounddevice.line24.comment PyPI wheels for Windows and macOS ship the sndfile shared library in _sounddevice_data directory,
# 017185.python.hook-sounddevice.line25.comment located next to the sounddevice.py module file (i.e., in the site-packages directory).
module_dir = pathlib.Path(get_module_file_attribute('sounddevice')).parent
data_dir = module_dir / '_sounddevice_data' / 'portaudio-binaries'
if data_dir.is_dir():
    destdir = str(data_dir.relative_to(module_dir))

    # 017186.python.hook-sounddevice.line31.comment Collect the shared library (known variants: libportaudio64bit.dll, libportaudio32bit.dll, libportaudio.dylib)
    for lib_file in data_dir.glob("libportaudio*.*"):
        binaries += [(str(lib_file), destdir)]

    # 017187.python.hook-sounddevice.line35.comment Collect the README.md file
    readme_file = data_dir / "README.md"
    if readme_file.is_file():
        datas += [(str(readme_file), destdir)]
else:
    # 017188.python.hook-sounddevice.line40.comment On linux and in Anaconda in all OSes, the system-installed portaudio library needs to be collected.
    def _find_system_portaudio_library():
        import os
        import ctypes.util
        from PyInstaller.depend.utils import _resolveCtypesImports

        libname = ctypes.util.find_library("portaudio")
        if libname is not None:
            resolved_binary = _resolveCtypesImports([os.path.basename(libname)])
            if resolved_binary:
                return resolved_binary[0][1]

    try:
        lib_file = _find_system_portaudio_library()
    except Exception as e:
        logger.warning("Error while trying to find system-installed portaudio library: %s", e)
        lib_file = None

    if lib_file:
        binaries += [(lib_file, '.')]

if not binaries:
    logger.warning("portaudio shared library not found - sounddevice will likely fail to work!")
