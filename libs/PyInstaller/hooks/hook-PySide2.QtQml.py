# 004353.python.hook-PySide2.QtQml.line1.comment -----------------------------------------------------------------------------
# 004354.python.hook-PySide2.QtQml.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004355.python.hook-PySide2.QtQml.line3.comment
# 004356.python.hook-PySide2.QtQml.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004357.python.hook-PySide2.QtQml.line5.comment or later) with exception for distributing the bootloader.
# 004358.python.hook-PySide2.QtQml.line6.comment
# 004359.python.hook-PySide2.QtQml.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004360.python.hook-PySide2.QtQml.line8.comment
# 004361.python.hook-PySide2.QtQml.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004362.python.hook-PySide2.QtQml.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies, pyside2_library_info

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
qml_binaries, qml_datas = pyside2_library_info.collect_qtqml_files()
binaries += qml_binaries
datas += qml_datas

hiddenimports += ["PySide2.QtGui"]
