# 005855.python.hook-gi.repository.GstInsertBin.line1.comment -----------------------------------------------------------------------------
# 005856.python.hook-gi.repository.GstInsertBin.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005857.python.hook-gi.repository.GstInsertBin.line3.comment
# 005858.python.hook-gi.repository.GstInsertBin.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005859.python.hook-gi.repository.GstInsertBin.line5.comment or later) with exception for distributing the bootloader.
# 005860.python.hook-gi.repository.GstInsertBin.line6.comment
# 005861.python.hook-gi.repository.GstInsertBin.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005862.python.hook-gi.repository.GstInsertBin.line8.comment
# 005863.python.hook-gi.repository.GstInsertBin.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005864.python.hook-gi.repository.GstInsertBin.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstInsertBin', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
