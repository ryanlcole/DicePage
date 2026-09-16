# 007601.python.hook-gi.repository.GstRtp.line1.comment -----------------------------------------------------------------------------
# 007602.python.hook-gi.repository.GstRtp.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007603.python.hook-gi.repository.GstRtp.line3.comment
# 007604.python.hook-gi.repository.GstRtp.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007605.python.hook-gi.repository.GstRtp.line5.comment or later) with exception for distributing the bootloader.
# 007606.python.hook-gi.repository.GstRtp.line6.comment
# 007607.python.hook-gi.repository.GstRtp.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007608.python.hook-gi.repository.GstRtp.line8.comment
# 007609.python.hook-gi.repository.GstRtp.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007610.python.hook-gi.repository.GstRtp.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007611.python.hook-gi.repository.GstRtp.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007612.python.hook-gi.repository.GstRtp.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
