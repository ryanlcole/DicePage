# 007685.python.hook-gi.repository.GstVulkan.line1.comment -----------------------------------------------------------------------------
# 007686.python.hook-gi.repository.GstVulkan.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007687.python.hook-gi.repository.GstVulkan.line3.comment
# 007688.python.hook-gi.repository.GstVulkan.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007689.python.hook-gi.repository.GstVulkan.line5.comment or later) with exception for distributing the bootloader.
# 007690.python.hook-gi.repository.GstVulkan.line6.comment
# 007691.python.hook-gi.repository.GstVulkan.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007692.python.hook-gi.repository.GstVulkan.line8.comment
# 007693.python.hook-gi.repository.GstVulkan.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007694.python.hook-gi.repository.GstVulkan.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007695.python.hook-gi.repository.GstVulkan.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007696.python.hook-gi.repository.GstVulkan.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
