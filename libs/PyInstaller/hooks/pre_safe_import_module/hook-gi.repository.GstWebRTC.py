# 007721.python.hook-gi.repository.GstWebRTC.line1.comment -----------------------------------------------------------------------------
# 007722.python.hook-gi.repository.GstWebRTC.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007723.python.hook-gi.repository.GstWebRTC.line3.comment
# 007724.python.hook-gi.repository.GstWebRTC.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007725.python.hook-gi.repository.GstWebRTC.line5.comment or later) with exception for distributing the bootloader.
# 007726.python.hook-gi.repository.GstWebRTC.line6.comment
# 007727.python.hook-gi.repository.GstWebRTC.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007728.python.hook-gi.repository.GstWebRTC.line8.comment
# 007729.python.hook-gi.repository.GstWebRTC.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007730.python.hook-gi.repository.GstWebRTC.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007731.python.hook-gi.repository.GstWebRTC.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007732.python.hook-gi.repository.GstWebRTC.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
