# 004250.python.hook-PySide2.QtHelp.line1.comment -----------------------------------------------------------------------------
# 004251.python.hook-PySide2.QtHelp.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004252.python.hook-PySide2.QtHelp.line3.comment
# 004253.python.hook-PySide2.QtHelp.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004254.python.hook-PySide2.QtHelp.line5.comment or later) with exception for distributing the bootloader.
# 004255.python.hook-PySide2.QtHelp.line6.comment
# 004256.python.hook-PySide2.QtHelp.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004257.python.hook-PySide2.QtHelp.line8.comment
# 004258.python.hook-PySide2.QtHelp.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004259.python.hook-PySide2.QtHelp.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
