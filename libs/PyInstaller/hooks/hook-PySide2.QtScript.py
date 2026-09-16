# 004403.python.hook-PySide2.QtScript.line1.comment -----------------------------------------------------------------------------
# 004404.python.hook-PySide2.QtScript.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004405.python.hook-PySide2.QtScript.line3.comment
# 004406.python.hook-PySide2.QtScript.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004407.python.hook-PySide2.QtScript.line5.comment or later) with exception for distributing the bootloader.
# 004408.python.hook-PySide2.QtScript.line6.comment
# 004409.python.hook-PySide2.QtScript.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004410.python.hook-PySide2.QtScript.line8.comment
# 004411.python.hook-PySide2.QtScript.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004412.python.hook-PySide2.QtScript.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
