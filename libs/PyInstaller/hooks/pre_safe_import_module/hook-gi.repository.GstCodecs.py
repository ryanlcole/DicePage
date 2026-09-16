# 007457.python.hook-gi.repository.GstCodecs.line1.comment -----------------------------------------------------------------------------
# 007458.python.hook-gi.repository.GstCodecs.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007459.python.hook-gi.repository.GstCodecs.line3.comment
# 007460.python.hook-gi.repository.GstCodecs.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007461.python.hook-gi.repository.GstCodecs.line5.comment or later) with exception for distributing the bootloader.
# 007462.python.hook-gi.repository.GstCodecs.line6.comment
# 007463.python.hook-gi.repository.GstCodecs.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007464.python.hook-gi.repository.GstCodecs.line8.comment
# 007465.python.hook-gi.repository.GstCodecs.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007466.python.hook-gi.repository.GstCodecs.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007467.python.hook-gi.repository.GstCodecs.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007468.python.hook-gi.repository.GstCodecs.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
