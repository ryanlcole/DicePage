# 003606.python.hook-PyQt6.Qsci.line1.comment -----------------------------------------------------------------------------
# 003607.python.hook-PyQt6.Qsci.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003608.python.hook-PyQt6.Qsci.line3.comment
# 003609.python.hook-PyQt6.Qsci.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003610.python.hook-PyQt6.Qsci.line5.comment or later) with exception for distributing the bootloader.
# 003611.python.hook-PyQt6.Qsci.line6.comment
# 003612.python.hook-PyQt6.Qsci.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003613.python.hook-PyQt6.Qsci.line8.comment
# 003614.python.hook-PyQt6.Qsci.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003615.python.hook-PyQt6.Qsci.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
