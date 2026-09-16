# 003838.python.hook-PyQt6.QtOpenGLWidgets.line1.comment -----------------------------------------------------------------------------
# 003839.python.hook-PyQt6.QtOpenGLWidgets.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 003840.python.hook-PyQt6.QtOpenGLWidgets.line3.comment
# 003841.python.hook-PyQt6.QtOpenGLWidgets.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003842.python.hook-PyQt6.QtOpenGLWidgets.line5.comment or later) with exception for distributing the bootloader.
# 003843.python.hook-PyQt6.QtOpenGLWidgets.line6.comment
# 003844.python.hook-PyQt6.QtOpenGLWidgets.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003845.python.hook-PyQt6.QtOpenGLWidgets.line8.comment
# 003846.python.hook-PyQt6.QtOpenGLWidgets.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003847.python.hook-PyQt6.QtOpenGLWidgets.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
