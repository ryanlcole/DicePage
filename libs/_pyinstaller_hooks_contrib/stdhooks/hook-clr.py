# 012553.python.hook-clr.line1.comment ------------------------------------------------------------------
# 012554.python.hook-clr.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012555.python.hook-clr.line3.comment
# 012556.python.hook-clr.line4.comment This file is distributed under the terms of the GNU General Public
# 012557.python.hook-clr.line5.comment License (version 2.0 or later).
# 012558.python.hook-clr.line6.comment
# 012559.python.hook-clr.line7.comment The full license is available in LICENSE, distributed with
# 012560.python.hook-clr.line8.comment this software.
# 012561.python.hook-clr.line9.comment
# 012562.python.hook-clr.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012563.python.hook-clr.line11.comment ------------------------------------------------------------------

# 012564.python.hook-clr.line13.comment There is a name clash between pythonnet's clr module/extension (which this hooks is for) and clr package that provides
# 012565.python.hook-clr.line14.comment the terminal styling library (https://pypi.org/project/clr/). Therefore, we must first check if pythonnet is actually
# 012566.python.hook-clr.line15.comment available...
from PyInstaller.utils.hooks import is_module_satisfies
from PyInstaller.compat import is_win

if is_module_satisfies("pythonnet"):
    # 012567.python.hook-clr.line20.comment pythonnet requires both clr.pyd and Python.Runtime.dll, but the latter isn't found by PyInstaller.
    import ctypes.util
    from PyInstaller.log import logger
    from _pyinstaller_hooks_contrib.compat import importlib_metadata

    collected_runtime_files = []

    # 012568.python.hook-clr.line27.comment Try finding Python.Runtime.dll via distribution's file list
    dist_files = importlib_metadata.files('pythonnet') or []
    runtime_dll_files = [f for f in dist_files if f.match('Python.Runtime.dll')]
    if len(runtime_dll_files) == 1:
        runtime_dll_file = runtime_dll_files[0]
        collected_runtime_files = [(runtime_dll_file.locate(), runtime_dll_file.parent.as_posix())]
        logger.debug("hook-clr: Python.Runtime.dll discovered via metadata.")
    elif len(runtime_dll_files) > 1:
        logger.warning("hook-clr: multiple instances of Python.Runtime.dll listed in metadata - cannot resolve.")

    # 012569.python.hook-clr.line37.comment Fall back to the legacy way
    if not collected_runtime_files:
        runtime_dll_file = ctypes.util.find_library('Python.Runtime')
        if runtime_dll_file:
            collected_runtime_files = [(runtime_dll_file, '.')]
            logger.debug('hook-clr: Python.Runtime.dll discovered via legacy method.')

    if not collected_runtime_files:
        raise Exception('Python.Runtime.dll not found')

    # 012570.python.hook-clr.line47.comment On Windows, collect runtime DLL file(s) as binaries; on other OSes, collect them as data files, to prevent fatal
    # 012571.python.hook-clr.line48.comment errors in binary dependency analysis.
    if is_win:
        binaries = collected_runtime_files
    else:
        datas = collected_runtime_files

    # 012572.python.hook-clr.line54.comment These modules are imported inside Python.Runtime.dll
    hiddenimports = ["platform", "warnings"]
