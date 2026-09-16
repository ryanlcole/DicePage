# 007697.python.hook-gi.repository.GstVulkanWayland.line1.comment -----------------------------------------------------------------------------
# 007698.python.hook-gi.repository.GstVulkanWayland.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007699.python.hook-gi.repository.GstVulkanWayland.line3.comment
# 007700.python.hook-gi.repository.GstVulkanWayland.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007701.python.hook-gi.repository.GstVulkanWayland.line5.comment or later) with exception for distributing the bootloader.
# 007702.python.hook-gi.repository.GstVulkanWayland.line6.comment
# 007703.python.hook-gi.repository.GstVulkanWayland.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007704.python.hook-gi.repository.GstVulkanWayland.line8.comment
# 007705.python.hook-gi.repository.GstVulkanWayland.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007706.python.hook-gi.repository.GstVulkanWayland.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007707.python.hook-gi.repository.GstVulkanWayland.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007708.python.hook-gi.repository.GstVulkanWayland.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
