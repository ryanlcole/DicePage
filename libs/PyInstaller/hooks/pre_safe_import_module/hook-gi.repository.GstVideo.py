# 007673.python.hook-gi.repository.GstVideo.line1.comment -----------------------------------------------------------------------------
# 007674.python.hook-gi.repository.GstVideo.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007675.python.hook-gi.repository.GstVideo.line3.comment
# 007676.python.hook-gi.repository.GstVideo.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007677.python.hook-gi.repository.GstVideo.line5.comment or later) with exception for distributing the bootloader.
# 007678.python.hook-gi.repository.GstVideo.line6.comment
# 007679.python.hook-gi.repository.GstVideo.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007680.python.hook-gi.repository.GstVideo.line8.comment
# 007681.python.hook-gi.repository.GstVideo.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007682.python.hook-gi.repository.GstVideo.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007683.python.hook-gi.repository.GstVideo.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert
    # 007684.python.hook-gi.repository.GstVideo.line15.comment them to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
