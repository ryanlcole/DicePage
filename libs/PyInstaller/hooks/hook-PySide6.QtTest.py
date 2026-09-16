# 005119.python.hook-PySide6.QtTest.line1.comment -----------------------------------------------------------------------------
# 005120.python.hook-PySide6.QtTest.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 005121.python.hook-PySide6.QtTest.line3.comment
# 005122.python.hook-PySide6.QtTest.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005123.python.hook-PySide6.QtTest.line5.comment or later) with exception for distributing the bootloader.
# 005124.python.hook-PySide6.QtTest.line6.comment
# 005125.python.hook-PySide6.QtTest.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005126.python.hook-PySide6.QtTest.line8.comment
# 005127.python.hook-PySide6.QtTest.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005128.python.hook-PySide6.QtTest.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
