# 004230.python.hook-PySide2.QtDataVisualization.line1.comment -----------------------------------------------------------------------------
# 004231.python.hook-PySide2.QtDataVisualization.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004232.python.hook-PySide2.QtDataVisualization.line3.comment
# 004233.python.hook-PySide2.QtDataVisualization.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004234.python.hook-PySide2.QtDataVisualization.line5.comment or later) with exception for distributing the bootloader.
# 004235.python.hook-PySide2.QtDataVisualization.line6.comment
# 004236.python.hook-PySide2.QtDataVisualization.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004237.python.hook-PySide2.QtDataVisualization.line8.comment
# 004238.python.hook-PySide2.QtDataVisualization.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004239.python.hook-PySide2.QtDataVisualization.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
