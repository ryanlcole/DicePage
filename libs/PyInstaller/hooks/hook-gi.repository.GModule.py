# 005601.python.hook-gi.repository.GModule.line1.comment -----------------------------------------------------------------------------
# 005602.python.hook-gi.repository.GModule.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005603.python.hook-gi.repository.GModule.line3.comment
# 005604.python.hook-gi.repository.GModule.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005605.python.hook-gi.repository.GModule.line5.comment or later) with exception for distributing the bootloader.
# 005606.python.hook-gi.repository.GModule.line6.comment
# 005607.python.hook-gi.repository.GModule.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005608.python.hook-gi.repository.GModule.line8.comment
# 005609.python.hook-gi.repository.GModule.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005610.python.hook-gi.repository.GModule.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GModule', '2.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
