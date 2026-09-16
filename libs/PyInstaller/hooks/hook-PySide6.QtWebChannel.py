# 005149.python.hook-PySide6.QtWebChannel.line1.comment -----------------------------------------------------------------------------
# 005150.python.hook-PySide6.QtWebChannel.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 005151.python.hook-PySide6.QtWebChannel.line3.comment
# 005152.python.hook-PySide6.QtWebChannel.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005153.python.hook-PySide6.QtWebChannel.line5.comment or later) with exception for distributing the bootloader.
# 005154.python.hook-PySide6.QtWebChannel.line6.comment
# 005155.python.hook-PySide6.QtWebChannel.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005156.python.hook-PySide6.QtWebChannel.line8.comment
# 005157.python.hook-PySide6.QtWebChannel.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005158.python.hook-PySide6.QtWebChannel.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
