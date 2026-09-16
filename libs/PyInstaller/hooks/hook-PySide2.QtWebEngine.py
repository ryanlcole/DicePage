# 004514.python.hook-PySide2.QtWebEngine.line1.comment -----------------------------------------------------------------------------
# 004515.python.hook-PySide2.QtWebEngine.line2.comment Copyright (c) 2014-2023, PyInstaller Development Team.
# 004516.python.hook-PySide2.QtWebEngine.line3.comment
# 004517.python.hook-PySide2.QtWebEngine.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004518.python.hook-PySide2.QtWebEngine.line5.comment or later) with exception for distributing the bootloader.
# 004519.python.hook-PySide2.QtWebEngine.line6.comment
# 004520.python.hook-PySide2.QtWebEngine.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004521.python.hook-PySide2.QtWebEngine.line8.comment
# 004522.python.hook-PySide2.QtWebEngine.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004523.python.hook-PySide2.QtWebEngine.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
