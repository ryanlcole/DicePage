# 003978.python.hook-PyQt6.QtStateMachine.line1.comment -----------------------------------------------------------------------------
# 003979.python.hook-PyQt6.QtStateMachine.line2.comment Copyright (c) 2025, PyInstaller Development Team.
# 003980.python.hook-PyQt6.QtStateMachine.line3.comment
# 003981.python.hook-PyQt6.QtStateMachine.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003982.python.hook-PyQt6.QtStateMachine.line5.comment or later) with exception for distributing the bootloader.
# 003983.python.hook-PyQt6.QtStateMachine.line6.comment
# 003984.python.hook-PyQt6.QtStateMachine.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003985.python.hook-PyQt6.QtStateMachine.line8.comment
# 003986.python.hook-PyQt6.QtStateMachine.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003987.python.hook-PyQt6.QtStateMachine.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)

# 003988.python.hook-PyQt6.QtStateMachine.line16.comment This dependency cannot seem to be inferred from linked libraries (at least on Windows).
hiddenimports += ['PyQt6.QtGui']
