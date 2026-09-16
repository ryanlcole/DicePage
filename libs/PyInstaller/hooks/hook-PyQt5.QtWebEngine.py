# 003455.python.hook-PyQt5.QtWebEngine.line1.comment -----------------------------------------------------------------------------
# 003456.python.hook-PyQt5.QtWebEngine.line2.comment Copyright (c) 2014-2023, PyInstaller Development Team.
# 003457.python.hook-PyQt5.QtWebEngine.line3.comment
# 003458.python.hook-PyQt5.QtWebEngine.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003459.python.hook-PyQt5.QtWebEngine.line5.comment or later) with exception for distributing the bootloader.
# 003460.python.hook-PyQt5.QtWebEngine.line6.comment
# 003461.python.hook-PyQt5.QtWebEngine.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003462.python.hook-PyQt5.QtWebEngine.line8.comment
# 003463.python.hook-PyQt5.QtWebEngine.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003464.python.hook-PyQt5.QtWebEngine.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
