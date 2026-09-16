# 003125.python.hook-PyQt5.Qt3DRender.line1.comment -----------------------------------------------------------------------------
# 003126.python.hook-PyQt5.Qt3DRender.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003127.python.hook-PyQt5.Qt3DRender.line3.comment
# 003128.python.hook-PyQt5.Qt3DRender.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003129.python.hook-PyQt5.Qt3DRender.line5.comment or later) with exception for distributing the bootloader.
# 003130.python.hook-PyQt5.Qt3DRender.line6.comment
# 003131.python.hook-PyQt5.Qt3DRender.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003132.python.hook-PyQt5.Qt3DRender.line8.comment
# 003133.python.hook-PyQt5.Qt3DRender.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003134.python.hook-PyQt5.Qt3DRender.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt5_dependencies

hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
