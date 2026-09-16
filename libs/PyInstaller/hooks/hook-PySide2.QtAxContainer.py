# 004190.python.hook-PySide2.QtAxContainer.line1.comment -----------------------------------------------------------------------------
# 004191.python.hook-PySide2.QtAxContainer.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004192.python.hook-PySide2.QtAxContainer.line3.comment
# 004193.python.hook-PySide2.QtAxContainer.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004194.python.hook-PySide2.QtAxContainer.line5.comment or later) with exception for distributing the bootloader.
# 004195.python.hook-PySide2.QtAxContainer.line6.comment
# 004196.python.hook-PySide2.QtAxContainer.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004197.python.hook-PySide2.QtAxContainer.line8.comment
# 004198.python.hook-PySide2.QtAxContainer.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004199.python.hook-PySide2.QtAxContainer.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
