# 007709.python.hook-gi.repository.GstVulkanXCB.line1.comment -----------------------------------------------------------------------------
# 007710.python.hook-gi.repository.GstVulkanXCB.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 007711.python.hook-gi.repository.GstVulkanXCB.line3.comment
# 007712.python.hook-gi.repository.GstVulkanXCB.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 007713.python.hook-gi.repository.GstVulkanXCB.line5.comment or later) with exception for distributing the bootloader.
# 007714.python.hook-gi.repository.GstVulkanXCB.line6.comment
# 007715.python.hook-gi.repository.GstVulkanXCB.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 007716.python.hook-gi.repository.GstVulkanXCB.line8.comment
# 007717.python.hook-gi.repository.GstVulkanXCB.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 007718.python.hook-gi.repository.GstVulkanXCB.line10.comment -----------------------------------------------------------------------------


def pre_safe_import_module(api):
    # 007719.python.hook-gi.repository.GstVulkanXCB.line14.comment PyGObject modules loaded through the gi repository are marked as MissingModules by modulegraph, so we convert them
    # 007720.python.hook-gi.repository.GstVulkanXCB.line15.comment to RuntimeModules in order for their hooks to be loaded and executed.
    api.add_runtime_module(api.module_name)
