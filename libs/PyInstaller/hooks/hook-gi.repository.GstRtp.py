# 005915.python.hook-gi.repository.GstRtp.line1.comment -----------------------------------------------------------------------------
# 005916.python.hook-gi.repository.GstRtp.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005917.python.hook-gi.repository.GstRtp.line3.comment
# 005918.python.hook-gi.repository.GstRtp.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005919.python.hook-gi.repository.GstRtp.line5.comment or later) with exception for distributing the bootloader.
# 005920.python.hook-gi.repository.GstRtp.line6.comment
# 005921.python.hook-gi.repository.GstRtp.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005922.python.hook-gi.repository.GstRtp.line8.comment
# 005923.python.hook-gi.repository.GstRtp.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005924.python.hook-gi.repository.GstRtp.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstRtp', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
