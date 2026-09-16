# 005925.python.hook-gi.repository.GstRtsp.line1.comment -----------------------------------------------------------------------------
# 005926.python.hook-gi.repository.GstRtsp.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005927.python.hook-gi.repository.GstRtsp.line3.comment
# 005928.python.hook-gi.repository.GstRtsp.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005929.python.hook-gi.repository.GstRtsp.line5.comment or later) with exception for distributing the bootloader.
# 005930.python.hook-gi.repository.GstRtsp.line6.comment
# 005931.python.hook-gi.repository.GstRtsp.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005932.python.hook-gi.repository.GstRtsp.line8.comment
# 005933.python.hook-gi.repository.GstRtsp.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005934.python.hook-gi.repository.GstRtsp.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstRtsp', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
