# 007625.python.hook-gi.repository.GstRtspServer.line1.comment -----------------------------------------------------------------------------
# 007626.python.hook-gi.repository.GstRtspServer.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007627.python.hook-gi.repository.GstRtspServer.line3.comment
# 007628.python.hook-gi.repository.GstRtspServer.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007629.python.hook-gi.repository.GstRtspServer.line5.comment or later) with exception for distributing the bootloader.
# 007630.python.hook-gi.repository.GstRtspServer.line6.comment
# 007631.python.hook-gi.repository.GstRtspServer.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007632.python.hook-gi.repository.GstRtspServer.line8.comment
# 007633.python.hook-gi.repository.GstRtspServer.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007634.python.hook-gi.repository.GstRtspServer.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007635.python.hook-gi.repository.GstRtspServer.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007636.python.hook-gi.repository.GstRtspServer.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
