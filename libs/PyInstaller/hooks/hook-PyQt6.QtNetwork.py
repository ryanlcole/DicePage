# 003798.python.hook-PyQt6.QtNetwork.line1.comment -----------------------------------------------------------------------------
# 003799.python.hook-PyQt6.QtNetwork.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 003800.python.hook-PyQt6.QtNetwork.line3.comment
# 003801.python.hook-PyQt6.QtNetwork.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003802.python.hook-PyQt6.QtNetwork.line5.comment or later) with exception for distributing the bootloader.
# 003803.python.hook-PyQt6.QtNetwork.line6.comment
# 003804.python.hook-PyQt6.QtNetwork.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003805.python.hook-PyQt6.QtNetwork.line8.comment
# 003806.python.hook-PyQt6.QtNetwork.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003807.python.hook-PyQt6.QtNetwork.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies, pyqt6_library_info

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
binaries += pyqt6_library_info.collect_qtnetwork_files()
