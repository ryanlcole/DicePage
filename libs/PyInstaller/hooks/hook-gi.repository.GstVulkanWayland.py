# 005995.python.hook-gi.repository.GstVulkanWayland.line1.comment -----------------------------------------------------------------------------
# 005996.python.hook-gi.repository.GstVulkanWayland.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005997.python.hook-gi.repository.GstVulkanWayland.line3.comment
# 005998.python.hook-gi.repository.GstVulkanWayland.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005999.python.hook-gi.repository.GstVulkanWayland.line5.comment or later) with exception for distributing the bootloader.
# 006000.python.hook-gi.repository.GstVulkanWayland.line6.comment
# 006001.python.hook-gi.repository.GstVulkanWayland.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006002.python.hook-gi.repository.GstVulkanWayland.line8.comment
# 006003.python.hook-gi.repository.GstVulkanWayland.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006004.python.hook-gi.repository.GstVulkanWayland.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstVulkanWayland', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
