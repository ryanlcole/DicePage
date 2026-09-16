# 004586.python.hook-PySide2.QtWinExtras.line1.comment -----------------------------------------------------------------------------
# 004587.python.hook-PySide2.QtWinExtras.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004588.python.hook-PySide2.QtWinExtras.line3.comment
# 004589.python.hook-PySide2.QtWinExtras.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004590.python.hook-PySide2.QtWinExtras.line5.comment or later) with exception for distributing the bootloader.
# 004591.python.hook-PySide2.QtWinExtras.line6.comment
# 004592.python.hook-PySide2.QtWinExtras.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004593.python.hook-PySide2.QtWinExtras.line8.comment
# 004594.python.hook-PySide2.QtWinExtras.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004595.python.hook-PySide2.QtWinExtras.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
