# 005945.python.hook-gi.repository.GstSdp.line1.comment -----------------------------------------------------------------------------
# 005946.python.hook-gi.repository.GstSdp.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005947.python.hook-gi.repository.GstSdp.line3.comment
# 005948.python.hook-gi.repository.GstSdp.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005949.python.hook-gi.repository.GstSdp.line5.comment or later) with exception for distributing the bootloader.
# 005950.python.hook-gi.repository.GstSdp.line6.comment
# 005951.python.hook-gi.repository.GstSdp.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005952.python.hook-gi.repository.GstSdp.line8.comment
# 005953.python.hook-gi.repository.GstSdp.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005954.python.hook-gi.repository.GstSdp.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstSdp', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
