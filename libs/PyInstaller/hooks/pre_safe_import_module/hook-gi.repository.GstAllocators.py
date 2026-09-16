# 007385.python.hook-gi.repository.GstAllocators.line1.comment -----------------------------------------------------------------------------
# 007386.python.hook-gi.repository.GstAllocators.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007387.python.hook-gi.repository.GstAllocators.line3.comment
# 007388.python.hook-gi.repository.GstAllocators.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007389.python.hook-gi.repository.GstAllocators.line5.comment or later) with exception for distributing the bootloader.
# 007390.python.hook-gi.repository.GstAllocators.line6.comment
# 007391.python.hook-gi.repository.GstAllocators.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007392.python.hook-gi.repository.GstAllocators.line8.comment
# 007393.python.hook-gi.repository.GstAllocators.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007394.python.hook-gi.repository.GstAllocators.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007395.python.hook-gi.repository.GstAllocators.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007396.python.hook-gi.repository.GstAllocators.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
