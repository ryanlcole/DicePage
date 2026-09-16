# 006087.python.hook-gi.repository.HarfBuzz.line1.comment -----------------------------------------------------------------------------
# 006088.python.hook-gi.repository.HarfBuzz.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 006089.python.hook-gi.repository.HarfBuzz.line3.comment
# 006090.python.hook-gi.repository.HarfBuzz.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006091.python.hook-gi.repository.HarfBuzz.line5.comment or later) with exception for distributing the bootloader.
# 006092.python.hook-gi.repository.HarfBuzz.line6.comment
# 006093.python.hook-gi.repository.HarfBuzz.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006094.python.hook-gi.repository.HarfBuzz.line8.comment
# 006095.python.hook-gi.repository.HarfBuzz.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006096.python.hook-gi.repository.HarfBuzz.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('HarfBuzz', '0.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
