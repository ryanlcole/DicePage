# 003255.python.hook-PyQt5.QtNetwork.line1.comment -----------------------------------------------------------------------------
# 003256.python.hook-PyQt5.QtNetwork.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003257.python.hook-PyQt5.QtNetwork.line3.comment
# 003258.python.hook-PyQt5.QtNetwork.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003259.python.hook-PyQt5.QtNetwork.line5.comment or later) with exception for distributing the bootloader.
# 003260.python.hook-PyQt5.QtNetwork.line6.comment
# 003261.python.hook-PyQt5.QtNetwork.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003262.python.hook-PyQt5.QtNetwork.line8.comment
# 003263.python.hook-PyQt5.QtNetwork.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003264.python.hook-PyQt5.QtNetwork.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies, pyqt5_library_info

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
binaries += pyqt5_library_info.collect_qtnetwork_files()
