# 003507.python.hook-PyQt5.QtWebSockets.line1.comment -----------------------------------------------------------------------------
# 003508.python.hook-PyQt5.QtWebSockets.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003509.python.hook-PyQt5.QtWebSockets.line3.comment
# 003510.python.hook-PyQt5.QtWebSockets.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003511.python.hook-PyQt5.QtWebSockets.line5.comment or later) with exception for distributing the bootloader.
# 003512.python.hook-PyQt5.QtWebSockets.line6.comment
# 003513.python.hook-PyQt5.QtWebSockets.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003514.python.hook-PyQt5.QtWebSockets.line8.comment
# 003515.python.hook-PyQt5.QtWebSockets.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003516.python.hook-PyQt5.QtWebSockets.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
