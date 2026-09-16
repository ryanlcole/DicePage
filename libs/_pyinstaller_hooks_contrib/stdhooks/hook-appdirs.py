# 011996.python.hook-appdirs.line1.comment ------------------------------------------------------------------
# 011997.python.hook-appdirs.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 011998.python.hook-appdirs.line3.comment
# 011999.python.hook-appdirs.line4.comment This file is distributed under the terms of the GNU General Public
# 012000.python.hook-appdirs.line5.comment License (version 2.0 or later).
# 012001.python.hook-appdirs.line6.comment
# 012002.python.hook-appdirs.line7.comment The full license is available in LICENSE, distributed with
# 012003.python.hook-appdirs.line8.comment this software.
# 012004.python.hook-appdirs.line9.comment
# 012005.python.hook-appdirs.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012006.python.hook-appdirs.line11.comment ------------------------------------------------------------------
"""
Import hook for appdirs.

On Windows, appdirs tries 2 different methods to get well-known directories
from the system: First with win32com, then with ctypes. Excluding win32com here
avoids including all the win32com related DLLs in programs that don't include
them otherwise.
"""

excludedimports = ['win32com']
