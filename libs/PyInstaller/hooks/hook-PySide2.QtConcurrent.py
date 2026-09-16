# 004210.python.hook-PySide2.QtConcurrent.line1.comment -----------------------------------------------------------------------------
# 004211.python.hook-PySide2.QtConcurrent.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004212.python.hook-PySide2.QtConcurrent.line3.comment
# 004213.python.hook-PySide2.QtConcurrent.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004214.python.hook-PySide2.QtConcurrent.line5.comment or later) with exception for distributing the bootloader.
# 004215.python.hook-PySide2.QtConcurrent.line6.comment
# 004216.python.hook-PySide2.QtConcurrent.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004217.python.hook-PySide2.QtConcurrent.line8.comment
# 004218.python.hook-PySide2.QtConcurrent.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004219.python.hook-PySide2.QtConcurrent.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
