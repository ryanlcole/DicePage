# 004200.python.hook-PySide2.QtCharts.line1.comment -----------------------------------------------------------------------------
# 004201.python.hook-PySide2.QtCharts.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004202.python.hook-PySide2.QtCharts.line3.comment
# 004203.python.hook-PySide2.QtCharts.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004204.python.hook-PySide2.QtCharts.line5.comment or later) with exception for distributing the bootloader.
# 004205.python.hook-PySide2.QtCharts.line6.comment
# 004206.python.hook-PySide2.QtCharts.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004207.python.hook-PySide2.QtCharts.line8.comment
# 004208.python.hook-PySide2.QtCharts.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004209.python.hook-PySide2.QtCharts.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
