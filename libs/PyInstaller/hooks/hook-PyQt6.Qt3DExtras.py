# 003636.python.hook-PyQt6.Qt3DExtras.line1.comment -----------------------------------------------------------------------------
# 003637.python.hook-PyQt6.Qt3DExtras.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 003638.python.hook-PyQt6.Qt3DExtras.line3.comment
# 003639.python.hook-PyQt6.Qt3DExtras.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 003640.python.hook-PyQt6.Qt3DExtras.line5.comment or later) with exception for distributing the bootloader.
# 003641.python.hook-PyQt6.Qt3DExtras.line6.comment
# 003642.python.hook-PyQt6.Qt3DExtras.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 003643.python.hook-PyQt6.Qt3DExtras.line8.comment
# 003644.python.hook-PyQt6.Qt3DExtras.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 003645.python.hook-PyQt6.Qt3DExtras.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
