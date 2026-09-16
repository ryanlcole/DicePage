# 005965.python.hook-gi.repository.GstTranscoder.line1.comment -----------------------------------------------------------------------------
# 005966.python.hook-gi.repository.GstTranscoder.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005967.python.hook-gi.repository.GstTranscoder.line3.comment
# 005968.python.hook-gi.repository.GstTranscoder.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005969.python.hook-gi.repository.GstTranscoder.line5.comment or later) with exception for distributing the bootloader.
# 005970.python.hook-gi.repository.GstTranscoder.line6.comment
# 005971.python.hook-gi.repository.GstTranscoder.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005972.python.hook-gi.repository.GstTranscoder.line8.comment
# 005973.python.hook-gi.repository.GstTranscoder.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005974.python.hook-gi.repository.GstTranscoder.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstTranscoder', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
