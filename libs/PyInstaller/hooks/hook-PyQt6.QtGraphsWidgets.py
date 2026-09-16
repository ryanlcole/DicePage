# 003747.python.hook-PyQt6.QtGraphsWidgets.line1.comment -----------------------------------------------------------------------------
# 003748.python.hook-PyQt6.QtGraphsWidgets.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 003749.python.hook-PyQt6.QtGraphsWidgets.line3.comment
# 003750.python.hook-PyQt6.QtGraphsWidgets.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003751.python.hook-PyQt6.QtGraphsWidgets.line5.comment or later) with exception for distributing the bootloader.
# 003752.python.hook-PyQt6.QtGraphsWidgets.line6.comment
# 003753.python.hook-PyQt6.QtGraphsWidgets.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003754.python.hook-PyQt6.QtGraphsWidgets.line8.comment
# 003755.python.hook-PyQt6.QtGraphsWidgets.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003756.python.hook-PyQt6.QtGraphsWidgets.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)

# 003757.python.hook-PyQt6.QtGraphsWidgets.line16.comment These dependencies cannot seem to be inferred from linked libraries.
hiddenimports += ['PyQt6.QtGraphs', 'PyQt6.QtQuickWidgets']
