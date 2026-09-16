# 003050.python.hook-PyQt5.Qsci.line1.comment -----------------------------------------------------------------------------
# 003051.python.hook-PyQt5.Qsci.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003052.python.hook-PyQt5.Qsci.line3.comment
# 003053.python.hook-PyQt5.Qsci.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003054.python.hook-PyQt5.Qsci.line5.comment or later) with exception for distributing the bootloader.
# 003055.python.hook-PyQt5.Qsci.line6.comment
# 003056.python.hook-PyQt5.Qsci.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003057.python.hook-PyQt5.Qsci.line8.comment
# 003058.python.hook-PyQt5.Qsci.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003059.python.hook-PyQt5.Qsci.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
