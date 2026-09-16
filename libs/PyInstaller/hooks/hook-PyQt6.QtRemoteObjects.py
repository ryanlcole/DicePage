# 003928.python.hook-PyQt6.QtRemoteObjects.line1.comment -----------------------------------------------------------------------------
# 003929.python.hook-PyQt6.QtRemoteObjects.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003930.python.hook-PyQt6.QtRemoteObjects.line3.comment
# 003931.python.hook-PyQt6.QtRemoteObjects.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003932.python.hook-PyQt6.QtRemoteObjects.line5.comment or later) with exception for distributing the bootloader.
# 003933.python.hook-PyQt6.QtRemoteObjects.line6.comment
# 003934.python.hook-PyQt6.QtRemoteObjects.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003935.python.hook-PyQt6.QtRemoteObjects.line8.comment
# 003936.python.hook-PyQt6.QtRemoteObjects.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003937.python.hook-PyQt6.QtRemoteObjects.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
