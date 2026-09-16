# 007637.python.hook-gi.repository.GstSdp.line1.comment -----------------------------------------------------------------------------
# 007638.python.hook-gi.repository.GstSdp.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007639.python.hook-gi.repository.GstSdp.line3.comment
# 007640.python.hook-gi.repository.GstSdp.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007641.python.hook-gi.repository.GstSdp.line5.comment or later) with exception for distributing the bootloader.
# 007642.python.hook-gi.repository.GstSdp.line6.comment
# 007643.python.hook-gi.repository.GstSdp.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007644.python.hook-gi.repository.GstSdp.line8.comment
# 007645.python.hook-gi.repository.GstSdp.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007646.python.hook-gi.repository.GstSdp.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007647.python.hook-gi.repository.GstSdp.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007648.python.hook-gi.repository.GstSdp.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
