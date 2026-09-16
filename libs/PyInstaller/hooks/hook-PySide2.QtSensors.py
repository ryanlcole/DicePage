# 004433.python.hook-PySide2.QtSensors.line1.comment -----------------------------------------------------------------------------
# 004434.python.hook-PySide2.QtSensors.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004435.python.hook-PySide2.QtSensors.line3.comment
# 004436.python.hook-PySide2.QtSensors.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004437.python.hook-PySide2.QtSensors.line5.comment or later) with exception for distributing the bootloader.
# 004438.python.hook-PySide2.QtSensors.line6.comment
# 004439.python.hook-PySide2.QtSensors.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004440.python.hook-PySide2.QtSensors.line8.comment
# 004441.python.hook-PySide2.QtSensors.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004442.python.hook-PySide2.QtSensors.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
