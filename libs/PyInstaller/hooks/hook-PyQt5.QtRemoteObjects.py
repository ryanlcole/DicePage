# 003365.python.hook-PyQt5.QtRemoteObjects.line1.comment -----------------------------------------------------------------------------
# 003366.python.hook-PyQt5.QtRemoteObjects.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003367.python.hook-PyQt5.QtRemoteObjects.line3.comment
# 003368.python.hook-PyQt5.QtRemoteObjects.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003369.python.hook-PyQt5.QtRemoteObjects.line5.comment or later) with exception for distributing the bootloader.
# 003370.python.hook-PyQt5.QtRemoteObjects.line6.comment
# 003371.python.hook-PyQt5.QtRemoteObjects.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003372.python.hook-PyQt5.QtRemoteObjects.line8.comment
# 003373.python.hook-PyQt5.QtRemoteObjects.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003374.python.hook-PyQt5.QtRemoteObjects.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
