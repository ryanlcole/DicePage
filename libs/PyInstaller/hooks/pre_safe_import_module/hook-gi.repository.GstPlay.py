# 007577.python.hook-gi.repository.GstPlay.line1.comment -----------------------------------------------------------------------------
# 007578.python.hook-gi.repository.GstPlay.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007579.python.hook-gi.repository.GstPlay.line3.comment
# 007580.python.hook-gi.repository.GstPlay.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007581.python.hook-gi.repository.GstPlay.line5.comment or later) with exception for distributing the bootloader.
# 007582.python.hook-gi.repository.GstPlay.line6.comment
# 007583.python.hook-gi.repository.GstPlay.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007584.python.hook-gi.repository.GstPlay.line8.comment
# 007585.python.hook-gi.repository.GstPlay.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007586.python.hook-gi.repository.GstPlay.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007587.python.hook-gi.repository.GstPlay.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007588.python.hook-gi.repository.GstPlay.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
