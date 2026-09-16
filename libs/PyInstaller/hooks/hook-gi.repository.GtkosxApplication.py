# 006077.python.hook-gi.repository.GtkosxApplication.line1.comment -----------------------------------------------------------------------------
# 006078.python.hook-gi.repository.GtkosxApplication.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 006079.python.hook-gi.repository.GtkosxApplication.line3.comment
# 006080.python.hook-gi.repository.GtkosxApplication.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006081.python.hook-gi.repository.GtkosxApplication.line5.comment or later) with exception for distributing the bootloader.
# 006082.python.hook-gi.repository.GtkosxApplication.line6.comment
# 006083.python.hook-gi.repository.GtkosxApplication.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006084.python.hook-gi.repository.GtkosxApplication.line8.comment
# 006085.python.hook-gi.repository.GtkosxApplication.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006086.python.hook-gi.repository.GtkosxApplication.line10.comment -----------------------------------------------------------------------------

from PyInstaller.compat import is_darwin
from PyInstaller.utils.hooks.gi import GiModuleInfo

if is_darwin:
    module_info = GiModuleInfo('GtkosxApplication', '1.0')
    if module_info.available:
        binaries, datas, hiddenimports = module_info.collect_typelib_data()
