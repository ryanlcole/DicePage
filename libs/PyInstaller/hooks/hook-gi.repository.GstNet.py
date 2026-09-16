# 005875.python.hook-gi.repository.GstNet.line1.comment -----------------------------------------------------------------------------
# 005876.python.hook-gi.repository.GstNet.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005877.python.hook-gi.repository.GstNet.line3.comment
# 005878.python.hook-gi.repository.GstNet.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005879.python.hook-gi.repository.GstNet.line5.comment or later) with exception for distributing the bootloader.
# 005880.python.hook-gi.repository.GstNet.line6.comment
# 005881.python.hook-gi.repository.GstNet.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005882.python.hook-gi.repository.GstNet.line8.comment
# 005883.python.hook-gi.repository.GstNet.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005884.python.hook-gi.repository.GstNet.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstNet', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
