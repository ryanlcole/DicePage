# 006051.python.hook-gi.repository.GtkClutter.line1.comment -----------------------------------------------------------------------------
# 006052.python.hook-gi.repository.GtkClutter.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 006053.python.hook-gi.repository.GtkClutter.line3.comment
# 006054.python.hook-gi.repository.GtkClutter.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006055.python.hook-gi.repository.GtkClutter.line5.comment or later) with exception for distributing the bootloader.
# 006056.python.hook-gi.repository.GtkClutter.line6.comment
# 006057.python.hook-gi.repository.GtkClutter.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006058.python.hook-gi.repository.GtkClutter.line8.comment
# 006059.python.hook-gi.repository.GtkClutter.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006060.python.hook-gi.repository.GtkClutter.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GtkClutter', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
