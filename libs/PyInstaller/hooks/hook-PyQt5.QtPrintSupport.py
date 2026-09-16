# 003305.python.hook-PyQt5.QtPrintSupport.line1.comment -----------------------------------------------------------------------------
# 003306.python.hook-PyQt5.QtPrintSupport.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003307.python.hook-PyQt5.QtPrintSupport.line3.comment
# 003308.python.hook-PyQt5.QtPrintSupport.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003309.python.hook-PyQt5.QtPrintSupport.line5.comment or later) with exception for distributing the bootloader.
# 003310.python.hook-PyQt5.QtPrintSupport.line6.comment
# 003311.python.hook-PyQt5.QtPrintSupport.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003312.python.hook-PyQt5.QtPrintSupport.line8.comment
# 003313.python.hook-PyQt5.QtPrintSupport.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003314.python.hook-PyQt5.QtPrintSupport.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
