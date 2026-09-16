# 006005.python.hook-gi.repository.GstVulkanXCB.line1.comment -----------------------------------------------------------------------------
# 006006.python.hook-gi.repository.GstVulkanXCB.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 006007.python.hook-gi.repository.GstVulkanXCB.line3.comment
# 006008.python.hook-gi.repository.GstVulkanXCB.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006009.python.hook-gi.repository.GstVulkanXCB.line5.comment or later) with exception for distributing the bootloader.
# 006010.python.hook-gi.repository.GstVulkanXCB.line6.comment
# 006011.python.hook-gi.repository.GstVulkanXCB.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006012.python.hook-gi.repository.GstVulkanXCB.line8.comment
# 006013.python.hook-gi.repository.GstVulkanXCB.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006014.python.hook-gi.repository.GstVulkanXCB.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstVulkanXCB', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
