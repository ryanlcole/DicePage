# 004566.python.hook-PySide2.QtWebSockets.line1.comment -----------------------------------------------------------------------------
# 004567.python.hook-PySide2.QtWebSockets.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004568.python.hook-PySide2.QtWebSockets.line3.comment
# 004569.python.hook-PySide2.QtWebSockets.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004570.python.hook-PySide2.QtWebSockets.line5.comment or later) with exception for distributing the bootloader.
# 004571.python.hook-PySide2.QtWebSockets.line6.comment
# 004572.python.hook-PySide2.QtWebSockets.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004573.python.hook-PySide2.QtWebSockets.line8.comment
# 004574.python.hook-PySide2.QtWebSockets.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004575.python.hook-PySide2.QtWebSockets.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
