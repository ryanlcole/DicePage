# 005745.python.hook-gi.repository.GstApp.line1.comment -----------------------------------------------------------------------------
# 005746.python.hook-gi.repository.GstApp.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005747.python.hook-gi.repository.GstApp.line3.comment
# 005748.python.hook-gi.repository.GstApp.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005749.python.hook-gi.repository.GstApp.line5.comment or later) with exception for distributing the bootloader.
# 005750.python.hook-gi.repository.GstApp.line6.comment
# 005751.python.hook-gi.repository.GstApp.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005752.python.hook-gi.repository.GstApp.line8.comment
# 005753.python.hook-gi.repository.GstApp.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005754.python.hook-gi.repository.GstApp.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstApp', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
