# 005059.python.hook-PySide6.QtSerialPort.line1.comment -----------------------------------------------------------------------------
# 005060.python.hook-PySide6.QtSerialPort.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 005061.python.hook-PySide6.QtSerialPort.line3.comment
# 005062.python.hook-PySide6.QtSerialPort.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005063.python.hook-PySide6.QtSerialPort.line5.comment or later) with exception for distributing the bootloader.
# 005064.python.hook-PySide6.QtSerialPort.line6.comment
# 005065.python.hook-PySide6.QtSerialPort.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005066.python.hook-PySide6.QtSerialPort.line8.comment
# 005067.python.hook-PySide6.QtSerialPort.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005068.python.hook-PySide6.QtSerialPort.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
