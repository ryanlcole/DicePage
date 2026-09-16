# 005705.python.hook-gi.repository.Gsk.line1.comment -----------------------------------------------------------------------------
# 005706.python.hook-gi.repository.Gsk.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005707.python.hook-gi.repository.Gsk.line3.comment
# 005708.python.hook-gi.repository.Gsk.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005709.python.hook-gi.repository.Gsk.line5.comment or later) with exception for distributing the bootloader.
# 005710.python.hook-gi.repository.Gsk.line6.comment
# 005711.python.hook-gi.repository.Gsk.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005712.python.hook-gi.repository.Gsk.line8.comment
# 005713.python.hook-gi.repository.Gsk.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005714.python.hook-gi.repository.Gsk.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('Gsk', '4.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
