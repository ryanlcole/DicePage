# 004240.python.hook-PySide2.QtGui.line1.comment -----------------------------------------------------------------------------
# 004241.python.hook-PySide2.QtGui.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004242.python.hook-PySide2.QtGui.line3.comment
# 004243.python.hook-PySide2.QtGui.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004244.python.hook-PySide2.QtGui.line5.comment or later) with exception for distributing the bootloader.
# 004245.python.hook-PySide2.QtGui.line6.comment
# 004246.python.hook-PySide2.QtGui.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004247.python.hook-PySide2.QtGui.line8.comment
# 004248.python.hook-PySide2.QtGui.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004249.python.hook-PySide2.QtGui.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
