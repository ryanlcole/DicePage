# 005865.python.hook-gi.repository.GstMpegts.line1.comment -----------------------------------------------------------------------------
# 005866.python.hook-gi.repository.GstMpegts.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005867.python.hook-gi.repository.GstMpegts.line3.comment
# 005868.python.hook-gi.repository.GstMpegts.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005869.python.hook-gi.repository.GstMpegts.line5.comment or later) with exception for distributing the bootloader.
# 005870.python.hook-gi.repository.GstMpegts.line6.comment
# 005871.python.hook-gi.repository.GstMpegts.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005872.python.hook-gi.repository.GstMpegts.line8.comment
# 005873.python.hook-gi.repository.GstMpegts.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005874.python.hook-gi.repository.GstMpegts.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstMpegts', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
