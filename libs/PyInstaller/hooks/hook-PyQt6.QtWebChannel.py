# 004029.python.hook-PyQt6.QtWebChannel.line1.comment -----------------------------------------------------------------------------
# 004030.python.hook-PyQt6.QtWebChannel.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004031.python.hook-PyQt6.QtWebChannel.line3.comment
# 004032.python.hook-PyQt6.QtWebChannel.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004033.python.hook-PyQt6.QtWebChannel.line5.comment or later) with exception for distributing the bootloader.
# 004034.python.hook-PyQt6.QtWebChannel.line6.comment
# 004035.python.hook-PyQt6.QtWebChannel.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004036.python.hook-PyQt6.QtWebChannel.line8.comment
# 004037.python.hook-PyQt6.QtWebChannel.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004038.python.hook-PyQt6.QtWebChannel.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
