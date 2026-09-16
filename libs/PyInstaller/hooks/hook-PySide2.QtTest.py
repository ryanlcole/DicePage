# 004473.python.hook-PySide2.QtTest.line1.comment -----------------------------------------------------------------------------
# 004474.python.hook-PySide2.QtTest.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004475.python.hook-PySide2.QtTest.line3.comment
# 004476.python.hook-PySide2.QtTest.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004477.python.hook-PySide2.QtTest.line5.comment or later) with exception for distributing the bootloader.
# 004478.python.hook-PySide2.QtTest.line6.comment
# 004479.python.hook-PySide2.QtTest.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004480.python.hook-PySide2.QtTest.line8.comment
# 004481.python.hook-PySide2.QtTest.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004482.python.hook-PySide2.QtTest.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
