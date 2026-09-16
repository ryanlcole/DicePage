# 007853.python.hook-gi.repository.cairo.line1.comment -----------------------------------------------------------------------------
# 007854.python.hook-gi.repository.cairo.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007855.python.hook-gi.repository.cairo.line3.comment
# 007856.python.hook-gi.repository.cairo.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007857.python.hook-gi.repository.cairo.line5.comment or later) with exception for distributing the bootloader.
# 007858.python.hook-gi.repository.cairo.line6.comment
# 007859.python.hook-gi.repository.cairo.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007860.python.hook-gi.repository.cairo.line8.comment
# 007861.python.hook-gi.repository.cairo.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007862.python.hook-gi.repository.cairo.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007863.python.hook-gi.repository.cairo.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007864.python.hook-gi.repository.cairo.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
