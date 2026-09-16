# 006147.python.hook-gi.repository.freetype2.line1.comment -----------------------------------------------------------------------------
# 006148.python.hook-gi.repository.freetype2.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 006149.python.hook-gi.repository.freetype2.line3.comment
# 006150.python.hook-gi.repository.freetype2.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006151.python.hook-gi.repository.freetype2.line5.comment or later) with exception for distributing the bootloader.
# 006152.python.hook-gi.repository.freetype2.line6.comment
# 006153.python.hook-gi.repository.freetype2.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006154.python.hook-gi.repository.freetype2.line8.comment
# 006155.python.hook-gi.repository.freetype2.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006156.python.hook-gi.repository.freetype2.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('freetype2', '2.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
