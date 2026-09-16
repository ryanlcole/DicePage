# 007361.python.hook-gi.repository.Gsk.line1.comment -----------------------------------------------------------------------------
# 007362.python.hook-gi.repository.Gsk.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007363.python.hook-gi.repository.Gsk.line3.comment
# 007364.python.hook-gi.repository.Gsk.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007365.python.hook-gi.repository.Gsk.line5.comment or later) with exception for distributing the bootloader.
# 007366.python.hook-gi.repository.Gsk.line6.comment
# 007367.python.hook-gi.repository.Gsk.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007368.python.hook-gi.repository.Gsk.line8.comment
# 007369.python.hook-gi.repository.Gsk.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007370.python.hook-gi.repository.Gsk.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007371.python.hook-gi.repository.Gsk.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007372.python.hook-gi.repository.Gsk.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
