# 003736.python.hook-PyQt6.QtGraphs.line1.comment -----------------------------------------------------------------------------
# 003737.python.hook-PyQt6.QtGraphs.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 003738.python.hook-PyQt6.QtGraphs.line3.comment
# 003739.python.hook-PyQt6.QtGraphs.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003740.python.hook-PyQt6.QtGraphs.line5.comment or later) with exception for distributing the bootloader.
# 003741.python.hook-PyQt6.QtGraphs.line6.comment
# 003742.python.hook-PyQt6.QtGraphs.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003743.python.hook-PyQt6.QtGraphs.line8.comment
# 003744.python.hook-PyQt6.QtGraphs.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003745.python.hook-PyQt6.QtGraphs.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)

# 003746.python.hook-PyQt6.QtGraphs.line16.comment These dependencies cannot seem to be inferred from linked libraries.
hiddenimports += ['PyQt6.QtNetwork', 'PyQt6.QtQml']
