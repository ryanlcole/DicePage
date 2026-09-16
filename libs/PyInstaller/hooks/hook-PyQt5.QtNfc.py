# 003275.python.hook-PyQt5.QtNfc.line1.comment -----------------------------------------------------------------------------
# 003276.python.hook-PyQt5.QtNfc.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003277.python.hook-PyQt5.QtNfc.line3.comment
# 003278.python.hook-PyQt5.QtNfc.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003279.python.hook-PyQt5.QtNfc.line5.comment or later) with exception for distributing the bootloader.
# 003280.python.hook-PyQt5.QtNfc.line6.comment
# 003281.python.hook-PyQt5.QtNfc.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003282.python.hook-PyQt5.QtNfc.line8.comment
# 003283.python.hook-PyQt5.QtNfc.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003284.python.hook-PyQt5.QtNfc.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
