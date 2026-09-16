# 007553.python.hook-gi.repository.GstNet.line1.comment -----------------------------------------------------------------------------
# 007554.python.hook-gi.repository.GstNet.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007555.python.hook-gi.repository.GstNet.line3.comment
# 007556.python.hook-gi.repository.GstNet.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007557.python.hook-gi.repository.GstNet.line5.comment or later) with exception for distributing the bootloader.
# 007558.python.hook-gi.repository.GstNet.line6.comment
# 007559.python.hook-gi.repository.GstNet.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007560.python.hook-gi.repository.GstNet.line8.comment
# 007561.python.hook-gi.repository.GstNet.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007562.python.hook-gi.repository.GstNet.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007563.python.hook-gi.repository.GstNet.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007564.python.hook-gi.repository.GstNet.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
