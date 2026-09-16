# 004009.python.hook-PyQt6.QtTest.line1.comment -----------------------------------------------------------------------------
# 004010.python.hook-PyQt6.QtTest.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 004011.python.hook-PyQt6.QtTest.line3.comment
# 004012.python.hook-PyQt6.QtTest.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004013.python.hook-PyQt6.QtTest.line5.comment or later) with exception for distributing the bootloader.
# 004014.python.hook-PyQt6.QtTest.line6.comment
# 004015.python.hook-PyQt6.QtTest.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004016.python.hook-PyQt6.QtTest.line8.comment
# 004017.python.hook-PyQt6.QtTest.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004018.python.hook-PyQt6.QtTest.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
