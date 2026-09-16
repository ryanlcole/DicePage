# 005775.python.hook-gi.repository.GstBase.line1.comment -----------------------------------------------------------------------------
# 005776.python.hook-gi.repository.GstBase.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005777.python.hook-gi.repository.GstBase.line3.comment
# 005778.python.hook-gi.repository.GstBase.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005779.python.hook-gi.repository.GstBase.line5.comment or later) with exception for distributing the bootloader.
# 005780.python.hook-gi.repository.GstBase.line6.comment
# 005781.python.hook-gi.repository.GstBase.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005782.python.hook-gi.repository.GstBase.line8.comment
# 005783.python.hook-gi.repository.GstBase.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005784.python.hook-gi.repository.GstBase.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstBase', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
