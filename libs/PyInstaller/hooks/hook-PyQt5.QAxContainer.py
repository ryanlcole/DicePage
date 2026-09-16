# 003040.python.hook-PyQt5.QAxContainer.line1.comment -----------------------------------------------------------------------------
# 003041.python.hook-PyQt5.QAxContainer.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003042.python.hook-PyQt5.QAxContainer.line3.comment
# 003043.python.hook-PyQt5.QAxContainer.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003044.python.hook-PyQt5.QAxContainer.line5.comment or later) with exception for distributing the bootloader.
# 003045.python.hook-PyQt5.QAxContainer.line6.comment
# 003046.python.hook-PyQt5.QAxContainer.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003047.python.hook-PyQt5.QAxContainer.line8.comment
# 003048.python.hook-PyQt5.QAxContainer.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003049.python.hook-PyQt5.QAxContainer.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
