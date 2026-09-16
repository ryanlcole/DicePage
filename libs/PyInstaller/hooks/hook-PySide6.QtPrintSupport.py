# 004959.python.hook-PySide6.QtPrintSupport.line1.comment -----------------------------------------------------------------------------
# 004960.python.hook-PySide6.QtPrintSupport.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 004961.python.hook-PySide6.QtPrintSupport.line3.comment
# 004962.python.hook-PySide6.QtPrintSupport.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004963.python.hook-PySide6.QtPrintSupport.line5.comment or later) with exception for distributing the bootloader.
# 004964.python.hook-PySide6.QtPrintSupport.line6.comment
# 004965.python.hook-PySide6.QtPrintSupport.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004966.python.hook-PySide6.QtPrintSupport.line8.comment
# 004967.python.hook-PySide6.QtPrintSupport.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004968.python.hook-PySide6.QtPrintSupport.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
