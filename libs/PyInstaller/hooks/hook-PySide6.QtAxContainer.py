# 004713.python.hook-PySide6.QtAxContainer.line1.comment -----------------------------------------------------------------------------
# 004714.python.hook-PySide6.QtAxContainer.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004715.python.hook-PySide6.QtAxContainer.line3.comment
# 004716.python.hook-PySide6.QtAxContainer.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004717.python.hook-PySide6.QtAxContainer.line5.comment or later) with exception for distributing the bootloader.
# 004718.python.hook-PySide6.QtAxContainer.line6.comment
# 004719.python.hook-PySide6.QtAxContainer.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004720.python.hook-PySide6.QtAxContainer.line8.comment
# 004721.python.hook-PySide6.QtAxContainer.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004722.python.hook-PySide6.QtAxContainer.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
