# 005548.python.hook-gi.repository.Champlain.line1.comment -----------------------------------------------------------------------------
# 005549.python.hook-gi.repository.Champlain.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005550.python.hook-gi.repository.Champlain.line3.comment
# 005551.python.hook-gi.repository.Champlain.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005552.python.hook-gi.repository.Champlain.line5.comment or later) with exception for distributing the bootloader.
# 005553.python.hook-gi.repository.Champlain.line6.comment
# 005554.python.hook-gi.repository.Champlain.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005555.python.hook-gi.repository.Champlain.line8.comment
# 005556.python.hook-gi.repository.Champlain.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005557.python.hook-gi.repository.Champlain.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('Champlain', '0.12')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
