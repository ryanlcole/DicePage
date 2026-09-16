# 007613.python.hook-gi.repository.GstRtsp.line1.comment -----------------------------------------------------------------------------
# 007614.python.hook-gi.repository.GstRtsp.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007615.python.hook-gi.repository.GstRtsp.line3.comment
# 007616.python.hook-gi.repository.GstRtsp.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007617.python.hook-gi.repository.GstRtsp.line5.comment or later) with exception for distributing the bootloader.
# 007618.python.hook-gi.repository.GstRtsp.line6.comment
# 007619.python.hook-gi.repository.GstRtsp.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007620.python.hook-gi.repository.GstRtsp.line8.comment
# 007621.python.hook-gi.repository.GstRtsp.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007622.python.hook-gi.repository.GstRtsp.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007623.python.hook-gi.repository.GstRtsp.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007624.python.hook-gi.repository.GstRtsp.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
