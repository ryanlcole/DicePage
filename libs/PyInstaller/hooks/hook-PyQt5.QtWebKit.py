# 003487.python.hook-PyQt5.QtWebKit.line1.comment -----------------------------------------------------------------------------
# 003488.python.hook-PyQt5.QtWebKit.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003489.python.hook-PyQt5.QtWebKit.line3.comment
# 003490.python.hook-PyQt5.QtWebKit.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003491.python.hook-PyQt5.QtWebKit.line5.comment or later) with exception for distributing the bootloader.
# 003492.python.hook-PyQt5.QtWebKit.line6.comment
# 003493.python.hook-PyQt5.QtWebKit.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003494.python.hook-PyQt5.QtWebKit.line8.comment
# 003495.python.hook-PyQt5.QtWebKit.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003496.python.hook-PyQt5.QtWebKit.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
