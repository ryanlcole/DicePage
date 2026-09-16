# 004270.python.hook-PySide2.QtMacExtras.line1.comment -----------------------------------------------------------------------------
# 004271.python.hook-PySide2.QtMacExtras.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004272.python.hook-PySide2.QtMacExtras.line3.comment
# 004273.python.hook-PySide2.QtMacExtras.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004274.python.hook-PySide2.QtMacExtras.line5.comment or later) with exception for distributing the bootloader.
# 004275.python.hook-PySide2.QtMacExtras.line6.comment
# 004276.python.hook-PySide2.QtMacExtras.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004277.python.hook-PySide2.QtMacExtras.line8.comment
# 004278.python.hook-PySide2.QtMacExtras.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004279.python.hook-PySide2.QtMacExtras.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
