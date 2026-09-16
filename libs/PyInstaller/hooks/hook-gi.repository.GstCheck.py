# 005785.python.hook-gi.repository.GstCheck.line1.comment -----------------------------------------------------------------------------
# 005786.python.hook-gi.repository.GstCheck.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005787.python.hook-gi.repository.GstCheck.line3.comment
# 005788.python.hook-gi.repository.GstCheck.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005789.python.hook-gi.repository.GstCheck.line5.comment or later) with exception for distributing the bootloader.
# 005790.python.hook-gi.repository.GstCheck.line6.comment
# 005791.python.hook-gi.repository.GstCheck.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005792.python.hook-gi.repository.GstCheck.line8.comment
# 005793.python.hook-gi.repository.GstCheck.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005794.python.hook-gi.repository.GstCheck.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstCheck', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
