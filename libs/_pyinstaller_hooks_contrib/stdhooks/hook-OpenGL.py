# 011815.python.hook-OpenGL.line1.comment ------------------------------------------------------------------
# 011816.python.hook-OpenGL.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 011817.python.hook-OpenGL.line3.comment
# 011818.python.hook-OpenGL.line4.comment This file is distributed under the terms of the GNU General Public
# 011819.python.hook-OpenGL.line5.comment License (version 2.0 or later).
# 011820.python.hook-OpenGL.line6.comment
# 011821.python.hook-OpenGL.line7.comment The full license is available in LICENSE, distributed with
# 011822.python.hook-OpenGL.line8.comment this software.
# 011823.python.hook-OpenGL.line9.comment
# 011824.python.hook-OpenGL.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 011825.python.hook-OpenGL.line11.comment ------------------------------------------------------------------
"""
Hook for PyOpenGL 3.x versions from 3.0.0b6 up. Previous versions have a
plugin system based on pkg_resources which is problematic to handle correctly
under pyinstaller; 2.x versions used to run fine without hooks, so this one
shouldn't hurt.
"""

from PyInstaller.compat import is_win, is_darwin
from PyInstaller.utils.hooks import collect_data_files, exec_statement
import os
import glob


def opengl_arrays_modules():
    """
    Return list of array modules for OpenGL module.
    e.g. 'OpenGL.arrays.vbo'
    """
    statement = 'import OpenGL; print(OpenGL.__path__[0])'
    opengl_mod_path = exec_statement(statement)
    arrays_mod_path = os.path.join(opengl_mod_path, 'arrays')
    files = glob.glob(arrays_mod_path + '/*.py')
    modules = []

    for f in files:
        mod = os.path.splitext(os.path.basename(f))[0]
        # 011826.python.hook-OpenGL.line38.comment Skip __init__ module.
        if mod == '__init__':
            continue
        modules.append('OpenGL.arrays.' + mod)

    return modules


# 011827.python.hook-OpenGL.line46.comment PlatformPlugin performs a conditional import based on os.name and
# 011828.python.hook-OpenGL.line47.comment sys.platform. PyInstaller misses this so let's add it ourselves...
if is_win:
    hiddenimports = ['OpenGL.platform.win32']
elif is_darwin:
    hiddenimports = ['OpenGL.platform.darwin']
# 011829.python.hook-OpenGL.line52.comment Use glx for other platforms (Linux, ...)
else:
    hiddenimports = ['OpenGL.platform.glx']

# 011830.python.hook-OpenGL.line56.comment Arrays modules are needed too.
hiddenimports += opengl_arrays_modules()

# 011831.python.hook-OpenGL.line59.comment PyOpenGL 3.x uses ctypes to load DLL libraries. PyOpenGL windows installer
# 011832.python.hook-OpenGL.line60.comment adds necessary dll files to
# 011833.python.hook-OpenGL.line61.comment DLL_DIRECTORY = os.path.join( os.path.dirname( OpenGL.__file__ ), 'DLLS')
# 011834.python.hook-OpenGL.line62.comment PyInstaller is not able to find these dlls. Just include them all as data
# 011835.python.hook-OpenGL.line63.comment files.
if is_win:
    datas = collect_data_files('OpenGL')
