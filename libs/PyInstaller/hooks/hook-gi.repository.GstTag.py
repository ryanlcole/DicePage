# 005955.python.hook-gi.repository.GstTag.line1.comment -----------------------------------------------------------------------------
# 005956.python.hook-gi.repository.GstTag.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005957.python.hook-gi.repository.GstTag.line3.comment
# 005958.python.hook-gi.repository.GstTag.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005959.python.hook-gi.repository.GstTag.line5.comment or later) with exception for distributing the bootloader.
# 005960.python.hook-gi.repository.GstTag.line6.comment
# 005961.python.hook-gi.repository.GstTag.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005962.python.hook-gi.repository.GstTag.line8.comment
# 005963.python.hook-gi.repository.GstTag.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005964.python.hook-gi.repository.GstTag.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstTag', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
