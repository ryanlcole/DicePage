# 004803.python.hook-PySide6.QtGraphsWidgets.line1.comment -----------------------------------------------------------------------------
# 004804.python.hook-PySide6.QtGraphsWidgets.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 004805.python.hook-PySide6.QtGraphsWidgets.line3.comment
# 004806.python.hook-PySide6.QtGraphsWidgets.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004807.python.hook-PySide6.QtGraphsWidgets.line5.comment or later) with exception for distributing the bootloader.
# 004808.python.hook-PySide6.QtGraphsWidgets.line6.comment
# 004809.python.hook-PySide6.QtGraphsWidgets.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004810.python.hook-PySide6.QtGraphsWidgets.line8.comment
# 004811.python.hook-PySide6.QtGraphsWidgets.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004812.python.hook-PySide6.QtGraphsWidgets.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)

# 004813.python.hook-PySide6.QtGraphsWidgets.line16.comment These dependencies cannot seem to be inferred from linked libraries.
hiddenimports += ['PySide6.QtQuickWidgets', 'PySide6.QtGraphs']
