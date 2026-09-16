# 006117.python.hook-gi.repository.PangoCairo.line1.comment -----------------------------------------------------------------------------
# 006118.python.hook-gi.repository.PangoCairo.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 006119.python.hook-gi.repository.PangoCairo.line3.comment
# 006120.python.hook-gi.repository.PangoCairo.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006121.python.hook-gi.repository.PangoCairo.line5.comment or later) with exception for distributing the bootloader.
# 006122.python.hook-gi.repository.PangoCairo.line6.comment
# 006123.python.hook-gi.repository.PangoCairo.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006124.python.hook-gi.repository.PangoCairo.line8.comment
# 006125.python.hook-gi.repository.PangoCairo.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006126.python.hook-gi.repository.PangoCairo.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('PangoCairo', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
