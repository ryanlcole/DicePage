# 005009.python.hook-PySide6.QtQuickWidgets.line1.comment -----------------------------------------------------------------------------
# 005010.python.hook-PySide6.QtQuickWidgets.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 005011.python.hook-PySide6.QtQuickWidgets.line3.comment
# 005012.python.hook-PySide6.QtQuickWidgets.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005013.python.hook-PySide6.QtQuickWidgets.line5.comment or later) with exception for distributing the bootloader.
# 005014.python.hook-PySide6.QtQuickWidgets.line6.comment
# 005015.python.hook-PySide6.QtQuickWidgets.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005016.python.hook-PySide6.QtQuickWidgets.line8.comment
# 005017.python.hook-PySide6.QtQuickWidgets.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005018.python.hook-PySide6.QtQuickWidgets.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
