# 007481.python.hook-gi.repository.GstGL.line1.comment -----------------------------------------------------------------------------
# 007482.python.hook-gi.repository.GstGL.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007483.python.hook-gi.repository.GstGL.line3.comment
# 007484.python.hook-gi.repository.GstGL.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007485.python.hook-gi.repository.GstGL.line5.comment or later) with exception for distributing the bootloader.
# 007486.python.hook-gi.repository.GstGL.line6.comment
# 007487.python.hook-gi.repository.GstGL.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007488.python.hook-gi.repository.GstGL.line8.comment
# 007489.python.hook-gi.repository.GstGL.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007490.python.hook-gi.repository.GstGL.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007491.python.hook-gi.repository.GstGL.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007492.python.hook-gi.repository.GstGL.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
