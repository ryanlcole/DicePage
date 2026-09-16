# 003527.python.hook-PyQt5.QtWinExtras.line1.comment -----------------------------------------------------------------------------
# 003528.python.hook-PyQt5.QtWinExtras.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003529.python.hook-PyQt5.QtWinExtras.line3.comment
# 003530.python.hook-PyQt5.QtWinExtras.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003531.python.hook-PyQt5.QtWinExtras.line5.comment or later) with exception for distributing the bootloader.
# 003532.python.hook-PyQt5.QtWinExtras.line6.comment
# 003533.python.hook-PyQt5.QtWinExtras.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003534.python.hook-PyQt5.QtWinExtras.line8.comment
# 003535.python.hook-PyQt5.QtWinExtras.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003536.python.hook-PyQt5.QtWinExtras.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
