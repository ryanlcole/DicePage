# 005905.python.hook-gi.repository.GstPlayer.line1.comment -----------------------------------------------------------------------------
# 005906.python.hook-gi.repository.GstPlayer.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005907.python.hook-gi.repository.GstPlayer.line3.comment
# 005908.python.hook-gi.repository.GstPlayer.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005909.python.hook-gi.repository.GstPlayer.line5.comment or later) with exception for distributing the bootloader.
# 005910.python.hook-gi.repository.GstPlayer.line6.comment
# 005911.python.hook-gi.repository.GstPlayer.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005912.python.hook-gi.repository.GstPlayer.line8.comment
# 005913.python.hook-gi.repository.GstPlayer.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005914.python.hook-gi.repository.GstPlayer.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstPlayer', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
