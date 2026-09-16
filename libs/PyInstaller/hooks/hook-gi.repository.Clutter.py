# 005558.python.hook-gi.repository.Clutter.line1.comment -----------------------------------------------------------------------------
# 005559.python.hook-gi.repository.Clutter.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005560.python.hook-gi.repository.Clutter.line3.comment
# 005561.python.hook-gi.repository.Clutter.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005562.python.hook-gi.repository.Clutter.line5.comment or later) with exception for distributing the bootloader.
# 005563.python.hook-gi.repository.Clutter.line6.comment
# 005564.python.hook-gi.repository.Clutter.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005565.python.hook-gi.repository.Clutter.line8.comment
# 005566.python.hook-gi.repository.Clutter.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005567.python.hook-gi.repository.Clutter.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('Clutter', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
