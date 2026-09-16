# 005805.python.hook-gi.repository.GstController.line1.comment -----------------------------------------------------------------------------
# 005806.python.hook-gi.repository.GstController.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005807.python.hook-gi.repository.GstController.line3.comment
# 005808.python.hook-gi.repository.GstController.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005809.python.hook-gi.repository.GstController.line5.comment or later) with exception for distributing the bootloader.
# 005810.python.hook-gi.repository.GstController.line6.comment
# 005811.python.hook-gi.repository.GstController.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005812.python.hook-gi.repository.GstController.line8.comment
# 005813.python.hook-gi.repository.GstController.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005814.python.hook-gi.repository.GstController.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstController', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
