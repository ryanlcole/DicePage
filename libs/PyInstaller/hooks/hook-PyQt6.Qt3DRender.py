# 003666.python.hook-PyQt6.Qt3DRender.line1.comment -----------------------------------------------------------------------------
# 003667.python.hook-PyQt6.Qt3DRender.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003668.python.hook-PyQt6.Qt3DRender.line3.comment
# 003669.python.hook-PyQt6.Qt3DRender.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003670.python.hook-PyQt6.Qt3DRender.line5.comment or later) with exception for distributing the bootloader.
# 003671.python.hook-PyQt6.Qt3DRender.line6.comment
# 003672.python.hook-PyQt6.Qt3DRender.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003673.python.hook-PyQt6.Qt3DRender.line8.comment
# 003674.python.hook-PyQt6.Qt3DRender.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003675.python.hook-PyQt6.Qt3DRender.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)

hiddenimports += ["PyQt6.QtOpenGL"]
