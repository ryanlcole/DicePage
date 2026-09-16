# 004413.python.hook-PySide2.QtScriptTools.line1.comment -----------------------------------------------------------------------------
# 004414.python.hook-PySide2.QtScriptTools.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004415.python.hook-PySide2.QtScriptTools.line3.comment
# 004416.python.hook-PySide2.QtScriptTools.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004417.python.hook-PySide2.QtScriptTools.line5.comment or later) with exception for distributing the bootloader.
# 004418.python.hook-PySide2.QtScriptTools.line6.comment
# 004419.python.hook-PySide2.QtScriptTools.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004420.python.hook-PySide2.QtScriptTools.line8.comment
# 004421.python.hook-PySide2.QtScriptTools.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004422.python.hook-PySide2.QtScriptTools.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
