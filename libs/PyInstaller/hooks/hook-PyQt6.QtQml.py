# 003888.python.hook-PyQt6.QtQml.line1.comment -----------------------------------------------------------------------------
# 003889.python.hook-PyQt6.QtQml.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 003890.python.hook-PyQt6.QtQml.line3.comment
# 003891.python.hook-PyQt6.QtQml.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003892.python.hook-PyQt6.QtQml.line5.comment or later) with exception for distributing the bootloader.
# 003893.python.hook-PyQt6.QtQml.line6.comment
# 003894.python.hook-PyQt6.QtQml.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003895.python.hook-PyQt6.QtQml.line8.comment
# 003896.python.hook-PyQt6.QtQml.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003897.python.hook-PyQt6.QtQml.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies, pyqt6_library_info

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
qml_binaries, qml_datas = pyqt6_library_info.collect_qtqml_files()
binaries += qml_binaries
datas += qml_datas
