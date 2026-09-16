# 004879.python.hook-PySide6.QtNetwork.line1.comment -----------------------------------------------------------------------------
# 004880.python.hook-PySide6.QtNetwork.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 004881.python.hook-PySide6.QtNetwork.line3.comment
# 004882.python.hook-PySide6.QtNetwork.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004883.python.hook-PySide6.QtNetwork.line5.comment or later) with exception for distributing the bootloader.
# 004884.python.hook-PySide6.QtNetwork.line6.comment
# 004885.python.hook-PySide6.QtNetwork.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004886.python.hook-PySide6.QtNetwork.line8.comment
# 004887.python.hook-PySide6.QtNetwork.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004888.python.hook-PySide6.QtNetwork.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies, pyside6_library_info

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
binaries += pyside6_library_info.collect_qtnetwork_files()
