# 005568.python.hook-gi.repository.DBus.line1.comment -----------------------------------------------------------------------------
# 005569.python.hook-gi.repository.DBus.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005570.python.hook-gi.repository.DBus.line3.comment
# 005571.python.hook-gi.repository.DBus.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005572.python.hook-gi.repository.DBus.line5.comment or later) with exception for distributing the bootloader.
# 005573.python.hook-gi.repository.DBus.line6.comment
# 005574.python.hook-gi.repository.DBus.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005575.python.hook-gi.repository.DBus.line8.comment
# 005576.python.hook-gi.repository.DBus.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005577.python.hook-gi.repository.DBus.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('DBus', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
