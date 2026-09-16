# 003497.python.hook-PyQt5.QtWebKitWidgets.line1.comment -----------------------------------------------------------------------------
# 003498.python.hook-PyQt5.QtWebKitWidgets.line2.comment Copyright (c) 2014-2023, PyInstaller Development Team.
# 003499.python.hook-PyQt5.QtWebKitWidgets.line3.comment
# 003500.python.hook-PyQt5.QtWebKitWidgets.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003501.python.hook-PyQt5.QtWebKitWidgets.line5.comment or later) with exception for distributing the bootloader.
# 003502.python.hook-PyQt5.QtWebKitWidgets.line6.comment
# 003503.python.hook-PyQt5.QtWebKitWidgets.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003504.python.hook-PyQt5.QtWebKitWidgets.line8.comment
# 003505.python.hook-PyQt5.QtWebKitWidgets.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003506.python.hook-PyQt5.QtWebKitWidgets.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
