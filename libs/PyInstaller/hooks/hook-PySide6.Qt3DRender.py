# 004700.python.hook-PySide6.Qt3DRender.line1.comment -----------------------------------------------------------------------------
# 004701.python.hook-PySide6.Qt3DRender.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004702.python.hook-PySide6.Qt3DRender.line3.comment
# 004703.python.hook-PySide6.Qt3DRender.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004704.python.hook-PySide6.Qt3DRender.line5.comment or later) with exception for distributing the bootloader.
# 004705.python.hook-PySide6.Qt3DRender.line6.comment
# 004706.python.hook-PySide6.Qt3DRender.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004707.python.hook-PySide6.Qt3DRender.line8.comment
# 004708.python.hook-PySide6.Qt3DRender.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004709.python.hook-PySide6.Qt3DRender.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies, pyside6_library_info

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)

# 004710.python.hook-PySide6.Qt3DRender.line16.comment In PySide 6.7.0, Qt3DRender module added a reference to QtOpenGL type system. The hidden import is required on
# 004711.python.hook-PySide6.Qt3DRender.line17.comment Windows, while on macOS and Linux we seem to pick it up automatically due to the corresponding Qt shared library
# 004712.python.hook-PySide6.Qt3DRender.line18.comment appearing among binary dependencies. Keep it around on all OSes, though - just in case this ever changes.
if pyside6_library_info.version is not None and pyside6_library_info.version >= [6, 7]:
    hiddenimports += ['PySide6.QtOpenGL']
