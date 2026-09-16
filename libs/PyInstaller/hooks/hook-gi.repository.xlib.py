# 006157.python.hook-gi.repository.xlib.line1.comment -----------------------------------------------------------------------------
# 006158.python.hook-gi.repository.xlib.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 006159.python.hook-gi.repository.xlib.line3.comment
# 006160.python.hook-gi.repository.xlib.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006161.python.hook-gi.repository.xlib.line5.comment or later) with exception for distributing the bootloader.
# 006162.python.hook-gi.repository.xlib.line6.comment
# 006163.python.hook-gi.repository.xlib.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006164.python.hook-gi.repository.xlib.line8.comment
# 006165.python.hook-gi.repository.xlib.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006166.python.hook-gi.repository.xlib.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('xlib', '2.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
