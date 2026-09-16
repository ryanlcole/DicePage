# 005578.python.hook-gi.repository.GIRepository.line1.comment -----------------------------------------------------------------------------
# 005579.python.hook-gi.repository.GIRepository.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005580.python.hook-gi.repository.GIRepository.line3.comment
# 005581.python.hook-gi.repository.GIRepository.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005582.python.hook-gi.repository.GIRepository.line5.comment or later) with exception for distributing the bootloader.
# 005583.python.hook-gi.repository.GIRepository.line6.comment
# 005584.python.hook-gi.repository.GIRepository.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005585.python.hook-gi.repository.GIRepository.line8.comment
# 005586.python.hook-gi.repository.GIRepository.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005587.python.hook-gi.repository.GIRepository.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GIRepository', '2.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
