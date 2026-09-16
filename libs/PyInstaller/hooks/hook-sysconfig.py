# 006952.python.hook-sysconfig.line1.comment -----------------------------------------------------------------------------
# 006953.python.hook-sysconfig.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 006954.python.hook-sysconfig.line3.comment
# 006955.python.hook-sysconfig.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006956.python.hook-sysconfig.line5.comment or later) with exception for distributing the bootloader.
# 006957.python.hook-sysconfig.line6.comment
# 006958.python.hook-sysconfig.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006959.python.hook-sysconfig.line8.comment
# 006960.python.hook-sysconfig.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006961.python.hook-sysconfig.line10.comment -----------------------------------------------------------------------------
import sys

# 006962.python.hook-sysconfig.line13.comment see https://github.com/python/cpython/blob/3.9/Lib/sysconfig.py#L593
# 006963.python.hook-sysconfig.line14.comment This will exclude `_osx_support`, `distutils`, `distutils.log` for sys.platform != 'darwin'
if sys.platform != 'darwin':
    excludedimports = ["_osx_support"]

# 006964.python.hook-sysconfig.line18.comment Python 3.6 uses additional modules like `_sysconfigdata_m_linux_x86_64-linux-gnu`, see
# 006965.python.hook-sysconfig.line19.comment https://github.com/python/cpython/blob/3.6/Lib/sysconfig.py#L417
# 006966.python.hook-sysconfig.line20.comment Note: Some versions of Anaconda backport this feature to before 3.6. See issue #3105.
# 006967.python.hook-sysconfig.line21.comment Note: on Windows, python.org and Anaconda python provide _get_sysconfigdata_name, but calling it fails due to sys
# 006968.python.hook-sysconfig.line22.comment module lacking abiflags attribute. It does work on MSYS2/MINGW python, where we need to collect corresponding file.
try:
    import sysconfig
    hiddenimports = [sysconfig._get_sysconfigdata_name()]
except AttributeError:
    # 006969.python.hook-sysconfig.line27.comment Either sysconfig has no attribute _get_sysconfigdata_name (i.e., the function does not exist), or this is Windows
    # 006970.python.hook-sysconfig.line28.comment and the _get_sysconfigdata_name() call failed due to missing sys.abiflags attribute.
    pass
