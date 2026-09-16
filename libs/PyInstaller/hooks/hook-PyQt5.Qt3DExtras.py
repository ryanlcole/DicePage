# 003095.python.hook-PyQt5.Qt3DExtras.line1.comment -----------------------------------------------------------------------------
# 003096.python.hook-PyQt5.Qt3DExtras.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003097.python.hook-PyQt5.Qt3DExtras.line3.comment
# 003098.python.hook-PyQt5.Qt3DExtras.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003099.python.hook-PyQt5.Qt3DExtras.line5.comment or later) with exception for distributing the bootloader.
# 003100.python.hook-PyQt5.Qt3DExtras.line6.comment
# 003101.python.hook-PyQt5.Qt3DExtras.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003102.python.hook-PyQt5.Qt3DExtras.line8.comment
# 003103.python.hook-PyQt5.Qt3DExtras.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003104.python.hook-PyQt5.Qt3DExtras.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
