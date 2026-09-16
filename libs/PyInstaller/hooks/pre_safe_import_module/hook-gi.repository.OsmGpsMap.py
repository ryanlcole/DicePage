# 007805.python.hook-gi.repository.OsmGpsMap.line1.comment -----------------------------------------------------------------------------
# 007806.python.hook-gi.repository.OsmGpsMap.line2.comment Copyright (c) 2025, PyInstaller Development Team.
# 007807.python.hook-gi.repository.OsmGpsMap.line3.comment
# 007808.python.hook-gi.repository.OsmGpsMap.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007809.python.hook-gi.repository.OsmGpsMap.line5.comment or later) with exception for distributing the bootloader.
# 007810.python.hook-gi.repository.OsmGpsMap.line6.comment
# 007811.python.hook-gi.repository.OsmGpsMap.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007812.python.hook-gi.repository.OsmGpsMap.line8.comment
# 007813.python.hook-gi.repository.OsmGpsMap.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007814.python.hook-gi.repository.OsmGpsMap.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007815.python.hook-gi.repository.OsmGpsMap.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007816.python.hook-gi.repository.OsmGpsMap.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
