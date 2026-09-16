# 005815.python.hook-gi.repository.GstGL.line1.comment -----------------------------------------------------------------------------
# 005816.python.hook-gi.repository.GstGL.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005817.python.hook-gi.repository.GstGL.line3.comment
# 005818.python.hook-gi.repository.GstGL.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005819.python.hook-gi.repository.GstGL.line5.comment or later) with exception for distributing the bootloader.
# 005820.python.hook-gi.repository.GstGL.line6.comment
# 005821.python.hook-gi.repository.GstGL.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005822.python.hook-gi.repository.GstGL.line8.comment
# 005823.python.hook-gi.repository.GstGL.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005824.python.hook-gi.repository.GstGL.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstGL', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
