# 006888.python.hook-shiboken6.line1.comment -----------------------------------------------------------------------------
# 006889.python.hook-shiboken6.line2.comment Copyright (c) 2023, PyInstaller Development Team.
# 006890.python.hook-shiboken6.line3.comment
# 006891.python.hook-shiboken6.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006892.python.hook-shiboken6.line5.comment or later) with exception for distributing the bootloader.
# 006893.python.hook-shiboken6.line6.comment
# 006894.python.hook-shiboken6.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006895.python.hook-shiboken6.line8.comment
# 006896.python.hook-shiboken6.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006897.python.hook-shiboken6.line10.comment -----------------------------------------------------------------------------

from PyInstaller import compat

# 006898.python.hook-shiboken6.line14.comment Up until python 3.12, `xxsubtype` was built-in on all OSes. Now it is an extension on non-Windows, and without it,
# 006899.python.hook-shiboken6.line15.comment shiboken6 initialization segfaults.
if compat.is_py312 and not compat.is_win:
    hiddenimports = ['xxsubtype']
