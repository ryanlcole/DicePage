# 004504.python.hook-PySide2.QtWebChannel.line1.comment -----------------------------------------------------------------------------
# 004505.python.hook-PySide2.QtWebChannel.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004506.python.hook-PySide2.QtWebChannel.line3.comment
# 004507.python.hook-PySide2.QtWebChannel.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004508.python.hook-PySide2.QtWebChannel.line5.comment or later) with exception for distributing the bootloader.
# 004509.python.hook-PySide2.QtWebChannel.line6.comment
# 004510.python.hook-PySide2.QtWebChannel.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004511.python.hook-PySide2.QtWebChannel.line8.comment
# 004512.python.hook-PySide2.QtWebChannel.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004513.python.hook-PySide2.QtWebChannel.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
