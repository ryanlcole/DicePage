# 007541.python.hook-gi.repository.GstMpegts.line1.comment -----------------------------------------------------------------------------
# 007542.python.hook-gi.repository.GstMpegts.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007543.python.hook-gi.repository.GstMpegts.line3.comment
# 007544.python.hook-gi.repository.GstMpegts.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007545.python.hook-gi.repository.GstMpegts.line5.comment or later) with exception for distributing the bootloader.
# 007546.python.hook-gi.repository.GstMpegts.line6.comment
# 007547.python.hook-gi.repository.GstMpegts.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007548.python.hook-gi.repository.GstMpegts.line8.comment
# 007549.python.hook-gi.repository.GstMpegts.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007550.python.hook-gi.repository.GstMpegts.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007551.python.hook-gi.repository.GstMpegts.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007552.python.hook-gi.repository.GstMpegts.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
