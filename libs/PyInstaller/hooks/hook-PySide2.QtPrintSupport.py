# 004343.python.hook-PySide2.QtPrintSupport.line1.comment -----------------------------------------------------------------------------
# 004344.python.hook-PySide2.QtPrintSupport.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004345.python.hook-PySide2.QtPrintSupport.line3.comment
# 004346.python.hook-PySide2.QtPrintSupport.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004347.python.hook-PySide2.QtPrintSupport.line5.comment or later) with exception for distributing the bootloader.
# 004348.python.hook-PySide2.QtPrintSupport.line6.comment
# 004349.python.hook-PySide2.QtPrintSupport.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004350.python.hook-PySide2.QtPrintSupport.line8.comment
# 004351.python.hook-PySide2.QtPrintSupport.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004352.python.hook-PySide2.QtPrintSupport.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
