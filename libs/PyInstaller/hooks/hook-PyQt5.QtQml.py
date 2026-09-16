# 003325.python.hook-PyQt5.QtQml.line1.comment -----------------------------------------------------------------------------
# 003326.python.hook-PyQt5.QtQml.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003327.python.hook-PyQt5.QtQml.line3.comment
# 003328.python.hook-PyQt5.QtQml.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003329.python.hook-PyQt5.QtQml.line5.comment or later) with exception for distributing the bootloader.
# 003330.python.hook-PyQt5.QtQml.line6.comment
# 003331.python.hook-PyQt5.QtQml.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003332.python.hook-PyQt5.QtQml.line8.comment
# 003333.python.hook-PyQt5.QtQml.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003334.python.hook-PyQt5.QtQml.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies, pyqt5_library_info

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
qml_binaries, qml_datas = pyqt5_library_info.collect_qtqml_files()
binaries += qml_binaries
datas += qml_datas
