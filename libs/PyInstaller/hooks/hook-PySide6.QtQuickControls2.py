# 004999.python.hook-PySide6.QtQuickControls2.line1.comment -----------------------------------------------------------------------------
# 005000.python.hook-PySide6.QtQuickControls2.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 005001.python.hook-PySide6.QtQuickControls2.line3.comment
# 005002.python.hook-PySide6.QtQuickControls2.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005003.python.hook-PySide6.QtQuickControls2.line5.comment or later) with exception for distributing the bootloader.
# 005004.python.hook-PySide6.QtQuickControls2.line6.comment
# 005005.python.hook-PySide6.QtQuickControls2.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005006.python.hook-PySide6.QtQuickControls2.line8.comment
# 005007.python.hook-PySide6.QtQuickControls2.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005008.python.hook-PySide6.QtQuickControls2.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)

hiddenimports += ['PySide6.QtQuick']
