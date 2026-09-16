# 006127.python.hook-gi.repository.Rsvg.line1.comment -----------------------------------------------------------------------------
# 006128.python.hook-gi.repository.Rsvg.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 006129.python.hook-gi.repository.Rsvg.line3.comment
# 006130.python.hook-gi.repository.Rsvg.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006131.python.hook-gi.repository.Rsvg.line5.comment or later) with exception for distributing the bootloader.
# 006132.python.hook-gi.repository.Rsvg.line6.comment
# 006133.python.hook-gi.repository.Rsvg.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006134.python.hook-gi.repository.Rsvg.line8.comment
# 006135.python.hook-gi.repository.Rsvg.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006136.python.hook-gi.repository.Rsvg.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('Rsvg', '2.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
