# 003445.python.hook-PyQt5.QtWebChannel.line1.comment -----------------------------------------------------------------------------
# 003446.python.hook-PyQt5.QtWebChannel.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003447.python.hook-PyQt5.QtWebChannel.line3.comment
# 003448.python.hook-PyQt5.QtWebChannel.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003449.python.hook-PyQt5.QtWebChannel.line5.comment or later) with exception for distributing the bootloader.
# 003450.python.hook-PyQt5.QtWebChannel.line6.comment
# 003451.python.hook-PyQt5.QtWebChannel.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003452.python.hook-PyQt5.QtWebChannel.line8.comment
# 003453.python.hook-PyQt5.QtWebChannel.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003454.python.hook-PyQt5.QtWebChannel.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
