# 003155.python.hook-PyQt5.QtCore.line1.comment -----------------------------------------------------------------------------
# 003156.python.hook-PyQt5.QtCore.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003157.python.hook-PyQt5.QtCore.line3.comment
# 003158.python.hook-PyQt5.QtCore.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003159.python.hook-PyQt5.QtCore.line5.comment or later) with exception for distributing the bootloader.
# 003160.python.hook-PyQt5.QtCore.line6.comment
# 003161.python.hook-PyQt5.QtCore.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003162.python.hook-PyQt5.QtCore.line8.comment
# 003163.python.hook-PyQt5.QtCore.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003164.python.hook-PyQt5.QtCore.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
