# 005611.python.hook-gi.repository.GObject.line1.comment -----------------------------------------------------------------------------
# 005612.python.hook-gi.repository.GObject.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005613.python.hook-gi.repository.GObject.line3.comment
# 005614.python.hook-gi.repository.GObject.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005615.python.hook-gi.repository.GObject.line5.comment or later) with exception for distributing the bootloader.
# 005616.python.hook-gi.repository.GObject.line6.comment
# 005617.python.hook-gi.repository.GObject.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005618.python.hook-gi.repository.GObject.line8.comment
# 005619.python.hook-gi.repository.GObject.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005620.python.hook-gi.repository.GObject.line10.comment -----------------------------------------------------------------------------
from PyInstaller.utils.hooks import check_requirement
from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GObject', '2.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
    # 005621.python.hook-gi.repository.GObject.line17.comment gi._gobject removed from PyGObject in version 3.25.1
    if check_requirement('PyGObject < 3.25.1'):
        hiddenimports += ['gi._gobject']
