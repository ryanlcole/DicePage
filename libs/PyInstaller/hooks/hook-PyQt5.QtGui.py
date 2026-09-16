# 003195.python.hook-PyQt5.QtGui.line1.comment -----------------------------------------------------------------------------
# 003196.python.hook-PyQt5.QtGui.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003197.python.hook-PyQt5.QtGui.line3.comment
# 003198.python.hook-PyQt5.QtGui.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003199.python.hook-PyQt5.QtGui.line5.comment or later) with exception for distributing the bootloader.
# 003200.python.hook-PyQt5.QtGui.line6.comment
# 003201.python.hook-PyQt5.QtGui.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003202.python.hook-PyQt5.QtGui.line8.comment
# 003203.python.hook-PyQt5.QtGui.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003204.python.hook-PyQt5.QtGui.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
