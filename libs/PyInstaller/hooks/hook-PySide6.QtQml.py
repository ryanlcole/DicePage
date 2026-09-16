# 004969.python.hook-PySide6.QtQml.line1.comment -----------------------------------------------------------------------------
# 004970.python.hook-PySide6.QtQml.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 004971.python.hook-PySide6.QtQml.line3.comment
# 004972.python.hook-PySide6.QtQml.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004973.python.hook-PySide6.QtQml.line5.comment or later) with exception for distributing the bootloader.
# 004974.python.hook-PySide6.QtQml.line6.comment
# 004975.python.hook-PySide6.QtQml.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004976.python.hook-PySide6.QtQml.line8.comment
# 004977.python.hook-PySide6.QtQml.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004978.python.hook-PySide6.QtQml.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies, pyside6_library_info

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
qml_binaries, qml_datas = pyside6_library_info.collect_qtqml_files()
binaries += qml_binaries
datas += qml_datas
