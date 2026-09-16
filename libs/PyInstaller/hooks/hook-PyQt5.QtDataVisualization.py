# 003175.python.hook-PyQt5.QtDataVisualization.line1.comment -----------------------------------------------------------------------------
# 003176.python.hook-PyQt5.QtDataVisualization.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003177.python.hook-PyQt5.QtDataVisualization.line3.comment
# 003178.python.hook-PyQt5.QtDataVisualization.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003179.python.hook-PyQt5.QtDataVisualization.line5.comment or later) with exception for distributing the bootloader.
# 003180.python.hook-PyQt5.QtDataVisualization.line6.comment
# 003181.python.hook-PyQt5.QtDataVisualization.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003182.python.hook-PyQt5.QtDataVisualization.line8.comment
# 003183.python.hook-PyQt5.QtDataVisualization.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003184.python.hook-PyQt5.QtDataVisualization.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
