# 003537.python.hook-PyQt5.QtX11Extras.line1.comment -----------------------------------------------------------------------------
# 003538.python.hook-PyQt5.QtX11Extras.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003539.python.hook-PyQt5.QtX11Extras.line3.comment
# 003540.python.hook-PyQt5.QtX11Extras.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003541.python.hook-PyQt5.QtX11Extras.line5.comment or later) with exception for distributing the bootloader.
# 003542.python.hook-PyQt5.QtX11Extras.line6.comment
# 003543.python.hook-PyQt5.QtX11Extras.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003544.python.hook-PyQt5.QtX11Extras.line8.comment
# 003545.python.hook-PyQt5.QtX11Extras.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003546.python.hook-PyQt5.QtX11Extras.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
