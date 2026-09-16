# 006137.python.hook-gi.repository.cairo.line1.comment -----------------------------------------------------------------------------
# 006138.python.hook-gi.repository.cairo.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 006139.python.hook-gi.repository.cairo.line3.comment
# 006140.python.hook-gi.repository.cairo.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006141.python.hook-gi.repository.cairo.line5.comment or later) with exception for distributing the bootloader.
# 006142.python.hook-gi.repository.cairo.line6.comment
# 006143.python.hook-gi.repository.cairo.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006144.python.hook-gi.repository.cairo.line8.comment
# 006145.python.hook-gi.repository.cairo.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006146.python.hook-gi.repository.cairo.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('cairo', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
