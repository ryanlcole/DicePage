# 003828.python.hook-PyQt6.QtOpenGL.line1.comment -----------------------------------------------------------------------------
# 003829.python.hook-PyQt6.QtOpenGL.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 003830.python.hook-PyQt6.QtOpenGL.line3.comment
# 003831.python.hook-PyQt6.QtOpenGL.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003832.python.hook-PyQt6.QtOpenGL.line5.comment or later) with exception for distributing the bootloader.
# 003833.python.hook-PyQt6.QtOpenGL.line6.comment
# 003834.python.hook-PyQt6.QtOpenGL.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003835.python.hook-PyQt6.QtOpenGL.line8.comment
# 003836.python.hook-PyQt6.QtOpenGL.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003837.python.hook-PyQt6.QtOpenGL.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
