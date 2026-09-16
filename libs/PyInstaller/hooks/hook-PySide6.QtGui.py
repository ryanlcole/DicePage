# 004814.python.hook-PySide6.QtGui.line1.comment -----------------------------------------------------------------------------
# 004815.python.hook-PySide6.QtGui.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 004816.python.hook-PySide6.QtGui.line3.comment
# 004817.python.hook-PySide6.QtGui.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004818.python.hook-PySide6.QtGui.line5.comment or later) with exception for distributing the bootloader.
# 004819.python.hook-PySide6.QtGui.line6.comment
# 004820.python.hook-PySide6.QtGui.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004821.python.hook-PySide6.QtGui.line8.comment
# 004822.python.hook-PySide6.QtGui.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004823.python.hook-PySide6.QtGui.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
