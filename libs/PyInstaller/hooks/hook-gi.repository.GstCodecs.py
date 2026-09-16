# 005795.python.hook-gi.repository.GstCodecs.line1.comment -----------------------------------------------------------------------------
# 005796.python.hook-gi.repository.GstCodecs.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005797.python.hook-gi.repository.GstCodecs.line3.comment
# 005798.python.hook-gi.repository.GstCodecs.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005799.python.hook-gi.repository.GstCodecs.line5.comment or later) with exception for distributing the bootloader.
# 005800.python.hook-gi.repository.GstCodecs.line6.comment
# 005801.python.hook-gi.repository.GstCodecs.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005802.python.hook-gi.repository.GstCodecs.line8.comment
# 005803.python.hook-gi.repository.GstCodecs.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005804.python.hook-gi.repository.GstCodecs.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstCodecs', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
