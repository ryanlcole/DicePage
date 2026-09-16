# 005985.python.hook-gi.repository.GstVulkan.line1.comment -----------------------------------------------------------------------------
# 005986.python.hook-gi.repository.GstVulkan.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005987.python.hook-gi.repository.GstVulkan.line3.comment
# 005988.python.hook-gi.repository.GstVulkan.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005989.python.hook-gi.repository.GstVulkan.line5.comment or later) with exception for distributing the bootloader.
# 005990.python.hook-gi.repository.GstVulkan.line6.comment
# 005991.python.hook-gi.repository.GstVulkan.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005992.python.hook-gi.repository.GstVulkan.line8.comment
# 005993.python.hook-gi.repository.GstVulkan.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005994.python.hook-gi.repository.GstVulkan.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstVulkan', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
