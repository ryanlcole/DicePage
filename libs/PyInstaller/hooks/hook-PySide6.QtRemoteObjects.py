# 005019.python.hook-PySide6.QtRemoteObjects.line1.comment -----------------------------------------------------------------------------
# 005020.python.hook-PySide6.QtRemoteObjects.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 005021.python.hook-PySide6.QtRemoteObjects.line3.comment
# 005022.python.hook-PySide6.QtRemoteObjects.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005023.python.hook-PySide6.QtRemoteObjects.line5.comment or later) with exception for distributing the bootloader.
# 005024.python.hook-PySide6.QtRemoteObjects.line6.comment
# 005025.python.hook-PySide6.QtRemoteObjects.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005026.python.hook-PySide6.QtRemoteObjects.line8.comment
# 005027.python.hook-PySide6.QtRemoteObjects.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005028.python.hook-PySide6.QtRemoteObjects.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
