# 003477.python.hook-PyQt5.QtWebEngineWidgets.line1.comment -----------------------------------------------------------------------------
# 003478.python.hook-PyQt5.QtWebEngineWidgets.line2.comment Copyright (c) 2014-2023, PyInstaller Development Team.
# 003479.python.hook-PyQt5.QtWebEngineWidgets.line3.comment
# 003480.python.hook-PyQt5.QtWebEngineWidgets.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003481.python.hook-PyQt5.QtWebEngineWidgets.line5.comment or later) with exception for distributing the bootloader.
# 003482.python.hook-PyQt5.QtWebEngineWidgets.line6.comment
# 003483.python.hook-PyQt5.QtWebEngineWidgets.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003484.python.hook-PyQt5.QtWebEngineWidgets.line8.comment
# 003485.python.hook-PyQt5.QtWebEngineWidgets.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003486.python.hook-PyQt5.QtWebEngineWidgets.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
