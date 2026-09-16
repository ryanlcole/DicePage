# 005735.python.hook-gi.repository.GstAllocators.line1.comment -----------------------------------------------------------------------------
# 005736.python.hook-gi.repository.GstAllocators.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005737.python.hook-gi.repository.GstAllocators.line3.comment
# 005738.python.hook-gi.repository.GstAllocators.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005739.python.hook-gi.repository.GstAllocators.line5.comment or later) with exception for distributing the bootloader.
# 005740.python.hook-gi.repository.GstAllocators.line6.comment
# 005741.python.hook-gi.repository.GstAllocators.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005742.python.hook-gi.repository.GstAllocators.line8.comment
# 005743.python.hook-gi.repository.GstAllocators.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005744.python.hook-gi.repository.GstAllocators.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstAllocators', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
