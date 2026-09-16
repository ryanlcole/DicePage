# 004636.python.hook-PySide2.line1.comment -----------------------------------------------------------------------------
# 004637.python.hook-PySide2.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 004638.python.hook-PySide2.line3.comment
# 004639.python.hook-PySide2.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004640.python.hook-PySide2.line5.comment or later) with exception for distributing the bootloader.
# 004641.python.hook-PySide2.line6.comment
# 004642.python.hook-PySide2.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004643.python.hook-PySide2.line8.comment
# 004644.python.hook-PySide2.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004645.python.hook-PySide2.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import pyside2_library_info, ensure_single_qt_bindings_package

# 004646.python.hook-PySide2.line14.comment Allow only one Qt bindings package to be collected in frozen application.
ensure_single_qt_bindings_package("PySide2")

# 004647.python.hook-PySide2.line17.comment Only proceed if PySide2 can be imported.
if pyside2_library_info.version is not None:
    hiddenimports = ['shiboken2', 'inspect']
    if pyside2_library_info.version < [5, 15]:
        # 004648.python.hook-PySide2.line21.comment The shiboken2 bootstrap in earlier releases requires __future__ in addition to inspect
        hiddenimports += ['__future__']

    # 004649.python.hook-PySide2.line24.comment Collect required Qt binaries.
    binaries = pyside2_library_info.collect_extra_binaries()
