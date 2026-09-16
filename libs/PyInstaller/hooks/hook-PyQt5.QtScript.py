# 003375.python.hook-PyQt5.QtScript.line1.comment -----------------------------------------------------------------------------
# 003376.python.hook-PyQt5.QtScript.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003377.python.hook-PyQt5.QtScript.line3.comment
# 003378.python.hook-PyQt5.QtScript.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003379.python.hook-PyQt5.QtScript.line5.comment or later) with exception for distributing the bootloader.
# 003380.python.hook-PyQt5.QtScript.line6.comment
# 003381.python.hook-PyQt5.QtScript.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003382.python.hook-PyQt5.QtScript.line8.comment
# 003383.python.hook-PyQt5.QtScript.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003384.python.hook-PyQt5.QtScript.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
