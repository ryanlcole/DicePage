# 003425.python.hook-PyQt5.QtTest.line1.comment -----------------------------------------------------------------------------
# 003426.python.hook-PyQt5.QtTest.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003427.python.hook-PyQt5.QtTest.line3.comment
# 003428.python.hook-PyQt5.QtTest.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003429.python.hook-PyQt5.QtTest.line5.comment or later) with exception for distributing the bootloader.
# 003430.python.hook-PyQt5.QtTest.line6.comment
# 003431.python.hook-PyQt5.QtTest.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003432.python.hook-PyQt5.QtTest.line8.comment
# 003433.python.hook-PyQt5.QtTest.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003434.python.hook-PyQt5.QtTest.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
