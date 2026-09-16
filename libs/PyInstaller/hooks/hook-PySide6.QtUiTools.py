# 005139.python.hook-PySide6.QtUiTools.line1.comment -----------------------------------------------------------------------------
# 005140.python.hook-PySide6.QtUiTools.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 005141.python.hook-PySide6.QtUiTools.line3.comment
# 005142.python.hook-PySide6.QtUiTools.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005143.python.hook-PySide6.QtUiTools.line5.comment or later) with exception for distributing the bootloader.
# 005144.python.hook-PySide6.QtUiTools.line6.comment
# 005145.python.hook-PySide6.QtUiTools.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005146.python.hook-PySide6.QtUiTools.line8.comment
# 005147.python.hook-PySide6.QtUiTools.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005148.python.hook-PySide6.QtUiTools.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
