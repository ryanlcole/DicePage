# 004443.python.hook-PySide2.QtSerialPort.line1.comment -----------------------------------------------------------------------------
# 004444.python.hook-PySide2.QtSerialPort.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004445.python.hook-PySide2.QtSerialPort.line3.comment
# 004446.python.hook-PySide2.QtSerialPort.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004447.python.hook-PySide2.QtSerialPort.line5.comment or later) with exception for distributing the bootloader.
# 004448.python.hook-PySide2.QtSerialPort.line6.comment
# 004449.python.hook-PySide2.QtSerialPort.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004450.python.hook-PySide2.QtSerialPort.line8.comment
# 004451.python.hook-PySide2.QtSerialPort.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004452.python.hook-PySide2.QtSerialPort.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
