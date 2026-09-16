# 003165.python.hook-PyQt5.QtDBus.line1.comment -----------------------------------------------------------------------------
# 003166.python.hook-PyQt5.QtDBus.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003167.python.hook-PyQt5.QtDBus.line3.comment
# 003168.python.hook-PyQt5.QtDBus.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003169.python.hook-PyQt5.QtDBus.line5.comment or later) with exception for distributing the bootloader.
# 003170.python.hook-PyQt5.QtDBus.line6.comment
# 003171.python.hook-PyQt5.QtDBus.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003172.python.hook-PyQt5.QtDBus.line8.comment
# 003173.python.hook-PyQt5.QtDBus.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003174.python.hook-PyQt5.QtDBus.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
