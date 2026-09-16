# 003878.python.hook-PyQt6.QtPrintSupport.line1.comment -----------------------------------------------------------------------------
# 003879.python.hook-PyQt6.QtPrintSupport.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 003880.python.hook-PyQt6.QtPrintSupport.line3.comment
# 003881.python.hook-PyQt6.QtPrintSupport.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003882.python.hook-PyQt6.QtPrintSupport.line5.comment or later) with exception for distributing the bootloader.
# 003883.python.hook-PyQt6.QtPrintSupport.line6.comment
# 003884.python.hook-PyQt6.QtPrintSupport.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003885.python.hook-PyQt6.QtPrintSupport.line8.comment
# 003886.python.hook-PyQt6.QtPrintSupport.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003887.python.hook-PyQt6.QtPrintSupport.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
