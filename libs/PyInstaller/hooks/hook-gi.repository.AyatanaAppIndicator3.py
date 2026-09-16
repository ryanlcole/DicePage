# 005538.python.hook-gi.repository.AyatanaAppIndicator3.line1.comment -----------------------------------------------------------------------------
# 005539.python.hook-gi.repository.AyatanaAppIndicator3.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005540.python.hook-gi.repository.AyatanaAppIndicator3.line3.comment
# 005541.python.hook-gi.repository.AyatanaAppIndicator3.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005542.python.hook-gi.repository.AyatanaAppIndicator3.line5.comment or later) with exception for distributing the bootloader.
# 005543.python.hook-gi.repository.AyatanaAppIndicator3.line6.comment
# 005544.python.hook-gi.repository.AyatanaAppIndicator3.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005545.python.hook-gi.repository.AyatanaAppIndicator3.line8.comment
# 005546.python.hook-gi.repository.AyatanaAppIndicator3.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005547.python.hook-gi.repository.AyatanaAppIndicator3.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('AyatanaAppIndicator3', '0.1')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
