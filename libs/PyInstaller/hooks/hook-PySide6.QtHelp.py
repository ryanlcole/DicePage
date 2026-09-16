# 004824.python.hook-PySide6.QtHelp.line1.comment -----------------------------------------------------------------------------
# 004825.python.hook-PySide6.QtHelp.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 004826.python.hook-PySide6.QtHelp.line3.comment
# 004827.python.hook-PySide6.QtHelp.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004828.python.hook-PySide6.QtHelp.line5.comment or later) with exception for distributing the bootloader.
# 004829.python.hook-PySide6.QtHelp.line6.comment
# 004830.python.hook-PySide6.QtHelp.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004831.python.hook-PySide6.QtHelp.line8.comment
# 004832.python.hook-PySide6.QtHelp.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004833.python.hook-PySide6.QtHelp.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
