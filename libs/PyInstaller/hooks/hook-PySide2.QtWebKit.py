# 004546.python.hook-PySide2.QtWebKit.line1.comment -----------------------------------------------------------------------------
# 004547.python.hook-PySide2.QtWebKit.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004548.python.hook-PySide2.QtWebKit.line3.comment
# 004549.python.hook-PySide2.QtWebKit.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004550.python.hook-PySide2.QtWebKit.line5.comment or later) with exception for distributing the bootloader.
# 004551.python.hook-PySide2.QtWebKit.line6.comment
# 004552.python.hook-PySide2.QtWebKit.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004553.python.hook-PySide2.QtWebKit.line8.comment
# 004554.python.hook-PySide2.QtWebKit.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004555.python.hook-PySide2.QtWebKit.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
