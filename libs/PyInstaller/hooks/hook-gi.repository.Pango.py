# 006107.python.hook-gi.repository.Pango.line1.comment -----------------------------------------------------------------------------
# 006108.python.hook-gi.repository.Pango.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 006109.python.hook-gi.repository.Pango.line3.comment
# 006110.python.hook-gi.repository.Pango.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006111.python.hook-gi.repository.Pango.line5.comment or later) with exception for distributing the bootloader.
# 006112.python.hook-gi.repository.Pango.line6.comment
# 006113.python.hook-gi.repository.Pango.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006114.python.hook-gi.repository.Pango.line8.comment
# 006115.python.hook-gi.repository.Pango.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006116.python.hook-gi.repository.Pango.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('Pango', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
