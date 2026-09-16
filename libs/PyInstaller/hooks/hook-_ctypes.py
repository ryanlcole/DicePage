# 005238.python.hook-_ctypes.line1.comment -----------------------------------------------------------------------------
# 005239.python.hook-_ctypes.line2.comment Copyright (c) 2014, PyInstaller Development Team.
# 005240.python.hook-_ctypes.line3.comment
# 005241.python.hook-_ctypes.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005242.python.hook-_ctypes.line5.comment or later) with exception for distributing the bootloader.
# 005243.python.hook-_ctypes.line6.comment
# 005244.python.hook-_ctypes.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005245.python.hook-_ctypes.line8.comment
# 005246.python.hook-_ctypes.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005247.python.hook-_ctypes.line10.comment -----------------------------------------------------------------------------

from PyInstaller import compat

# 005248.python.hook-_ctypes.line14.comment During python 3.14 development cycle, ctypes struct/union layout logic has been moved from `_ctypes` extension into
# 005249.python.hook-_ctypes.line15.comment Python, i.e., `ctypes._layout` module: https://github.com/python/cpython/pull/123352
# 005250.python.hook-_ctypes.line16.comment Since this module is referenced only from the `_ctypes` extension, it needs to be added to hidden imports, at least on
# 005251.python.hook-_ctypes.line17.comment Windows and macOS.
if compat.is_py314:
    hiddenimports = ['ctypes._layout']
