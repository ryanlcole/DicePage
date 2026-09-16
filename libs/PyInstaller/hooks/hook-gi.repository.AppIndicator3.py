# 005517.python.hook-gi.repository.AppIndicator3.line1.comment -----------------------------------------------------------------------------
# 005518.python.hook-gi.repository.AppIndicator3.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005519.python.hook-gi.repository.AppIndicator3.line3.comment
# 005520.python.hook-gi.repository.AppIndicator3.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005521.python.hook-gi.repository.AppIndicator3.line5.comment or later) with exception for distributing the bootloader.
# 005522.python.hook-gi.repository.AppIndicator3.line6.comment
# 005523.python.hook-gi.repository.AppIndicator3.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005524.python.hook-gi.repository.AppIndicator3.line8.comment
# 005525.python.hook-gi.repository.AppIndicator3.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005526.python.hook-gi.repository.AppIndicator3.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('AppIndicator3', '0.1')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
