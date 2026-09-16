# 003225.python.hook-PyQt5.QtMacExtras.line1.comment -----------------------------------------------------------------------------
# 003226.python.hook-PyQt5.QtMacExtras.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003227.python.hook-PyQt5.QtMacExtras.line3.comment
# 003228.python.hook-PyQt5.QtMacExtras.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003229.python.hook-PyQt5.QtMacExtras.line5.comment or later) with exception for distributing the bootloader.
# 003230.python.hook-PyQt5.QtMacExtras.line6.comment
# 003231.python.hook-PyQt5.QtMacExtras.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003232.python.hook-PyQt5.QtMacExtras.line8.comment
# 003233.python.hook-PyQt5.QtMacExtras.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003234.python.hook-PyQt5.QtMacExtras.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
