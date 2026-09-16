# 006097.python.hook-gi.repository.OsmGpsMap.line1.comment -----------------------------------------------------------------------------
# 006098.python.hook-gi.repository.OsmGpsMap.line2.comment Copyright (c) 2025, PyInstaller Development Team.
# 006099.python.hook-gi.repository.OsmGpsMap.line3.comment
# 006100.python.hook-gi.repository.OsmGpsMap.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006101.python.hook-gi.repository.OsmGpsMap.line5.comment or later) with exception for distributing the bootloader.
# 006102.python.hook-gi.repository.OsmGpsMap.line6.comment
# 006103.python.hook-gi.repository.OsmGpsMap.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006104.python.hook-gi.repository.OsmGpsMap.line8.comment
# 006105.python.hook-gi.repository.OsmGpsMap.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006106.python.hook-gi.repository.OsmGpsMap.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo("OsmGpsMap", "1.0")
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
