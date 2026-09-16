# 004493.python.hook-PySide2.QtUiTools.line1.comment -----------------------------------------------------------------------------
# 004494.python.hook-PySide2.QtUiTools.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 004495.python.hook-PySide2.QtUiTools.line3.comment
# 004496.python.hook-PySide2.QtUiTools.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004497.python.hook-PySide2.QtUiTools.line5.comment or later) with exception for distributing the bootloader.
# 004498.python.hook-PySide2.QtUiTools.line6.comment
# 004499.python.hook-PySide2.QtUiTools.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004500.python.hook-PySide2.QtUiTools.line8.comment
# 004501.python.hook-PySide2.QtUiTools.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004502.python.hook-PySide2.QtUiTools.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
hiddenimports += ['PySide2.QtXml']  # Not inferred from dynamic lib analysis
