# 004834.python.hook-PySide6.QtHttpServer.line1.comment -----------------------------------------------------------------------------
# 004835.python.hook-PySide6.QtHttpServer.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004836.python.hook-PySide6.QtHttpServer.line3.comment
# 004837.python.hook-PySide6.QtHttpServer.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004838.python.hook-PySide6.QtHttpServer.line5.comment or later) with exception for distributing the bootloader.
# 004839.python.hook-PySide6.QtHttpServer.line6.comment
# 004840.python.hook-PySide6.QtHttpServer.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004841.python.hook-PySide6.QtHttpServer.line8.comment
# 004842.python.hook-PySide6.QtHttpServer.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004843.python.hook-PySide6.QtHttpServer.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)

# 004844.python.hook-PySide6.QtHttpServer.line16.comment This seems to be necessary on Windows; on other OSes, it is inferred automatically because the extension is linked
# 004845.python.hook-PySide6.QtHttpServer.line17.comment against the Qt6Concurrent shared library.
hiddenimports += ['PySide6.QtConcurrent']
