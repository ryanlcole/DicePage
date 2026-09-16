# 003696.python.hook-PyQt6.QtCore.line1.comment -----------------------------------------------------------------------------
# 003697.python.hook-PyQt6.QtCore.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 003698.python.hook-PyQt6.QtCore.line3.comment
# 003699.python.hook-PyQt6.QtCore.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003700.python.hook-PyQt6.QtCore.line5.comment or later) with exception for distributing the bootloader.
# 003701.python.hook-PyQt6.QtCore.line6.comment
# 003702.python.hook-PyQt6.QtCore.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003703.python.hook-PyQt6.QtCore.line8.comment
# 003704.python.hook-PyQt6.QtCore.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003705.python.hook-PyQt6.QtCore.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
