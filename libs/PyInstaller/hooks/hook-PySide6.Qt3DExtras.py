# 004670.python.hook-PySide6.Qt3DExtras.line1.comment -----------------------------------------------------------------------------
# 004671.python.hook-PySide6.Qt3DExtras.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004672.python.hook-PySide6.Qt3DExtras.line3.comment
# 004673.python.hook-PySide6.Qt3DExtras.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004674.python.hook-PySide6.Qt3DExtras.line5.comment or later) with exception for distributing the bootloader.
# 004675.python.hook-PySide6.Qt3DExtras.line6.comment
# 004676.python.hook-PySide6.Qt3DExtras.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004677.python.hook-PySide6.Qt3DExtras.line8.comment
# 004678.python.hook-PySide6.Qt3DExtras.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004679.python.hook-PySide6.Qt3DExtras.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
