# 005507.python.hook-gi.repository.Adw.line1.comment -----------------------------------------------------------------------------
# 005508.python.hook-gi.repository.Adw.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005509.python.hook-gi.repository.Adw.line3.comment
# 005510.python.hook-gi.repository.Adw.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005511.python.hook-gi.repository.Adw.line5.comment or later) with exception for distributing the bootloader.
# 005512.python.hook-gi.repository.Adw.line6.comment
# 005513.python.hook-gi.repository.Adw.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005514.python.hook-gi.repository.Adw.line8.comment
# 005515.python.hook-gi.repository.Adw.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005516.python.hook-gi.repository.Adw.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('Adw', '1')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
