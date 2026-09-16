# 004220.python.hook-PySide2.QtCore.line1.comment -----------------------------------------------------------------------------
# 004221.python.hook-PySide2.QtCore.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004222.python.hook-PySide2.QtCore.line3.comment
# 004223.python.hook-PySide2.QtCore.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004224.python.hook-PySide2.QtCore.line5.comment or later) with exception for distributing the bootloader.
# 004225.python.hook-PySide2.QtCore.line6.comment
# 004226.python.hook-PySide2.QtCore.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004227.python.hook-PySide2.QtCore.line8.comment
# 004228.python.hook-PySide2.QtCore.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004229.python.hook-PySide2.QtCore.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
