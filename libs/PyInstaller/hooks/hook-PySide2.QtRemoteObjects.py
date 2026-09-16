# 004393.python.hook-PySide2.QtRemoteObjects.line1.comment -----------------------------------------------------------------------------
# 004394.python.hook-PySide2.QtRemoteObjects.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 004395.python.hook-PySide2.QtRemoteObjects.line3.comment
# 004396.python.hook-PySide2.QtRemoteObjects.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 004397.python.hook-PySide2.QtRemoteObjects.line5.comment or later) with exception for distributing the bootloader.
# 004398.python.hook-PySide2.QtRemoteObjects.line6.comment
# 004399.python.hook-PySide2.QtRemoteObjects.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 004400.python.hook-PySide2.QtRemoteObjects.line8.comment
# 004401.python.hook-PySide2.QtRemoteObjects.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 004402.python.hook-PySide2.QtRemoteObjects.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
