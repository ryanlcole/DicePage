# 003768.python.hook-PyQt6.QtHelp.line1.comment -----------------------------------------------------------------------------
# 003769.python.hook-PyQt6.QtHelp.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 003770.python.hook-PyQt6.QtHelp.line3.comment
# 003771.python.hook-PyQt6.QtHelp.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003772.python.hook-PyQt6.QtHelp.line5.comment or later) with exception for distributing the bootloader.
# 003773.python.hook-PyQt6.QtHelp.line6.comment
# 003774.python.hook-PyQt6.QtHelp.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003775.python.hook-PyQt6.QtHelp.line8.comment
# 003776.python.hook-PyQt6.QtHelp.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003777.python.hook-PyQt6.QtHelp.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
