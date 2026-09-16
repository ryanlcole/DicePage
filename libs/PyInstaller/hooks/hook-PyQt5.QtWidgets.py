# 003517.python.hook-PyQt5.QtWidgets.line1.comment -----------------------------------------------------------------------------
# 003518.python.hook-PyQt5.QtWidgets.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003519.python.hook-PyQt5.QtWidgets.line3.comment
# 003520.python.hook-PyQt5.QtWidgets.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003521.python.hook-PyQt5.QtWidgets.line5.comment or later) with exception for distributing the bootloader.
# 003522.python.hook-PyQt5.QtWidgets.line6.comment
# 003523.python.hook-PyQt5.QtWidgets.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003524.python.hook-PyQt5.QtWidgets.line8.comment
# 003525.python.hook-PyQt5.QtWidgets.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003526.python.hook-PyQt5.QtWidgets.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
