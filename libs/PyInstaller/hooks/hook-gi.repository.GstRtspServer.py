# 005935.python.hook-gi.repository.GstRtspServer.line1.comment -----------------------------------------------------------------------------
# 005936.python.hook-gi.repository.GstRtspServer.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005937.python.hook-gi.repository.GstRtspServer.line3.comment
# 005938.python.hook-gi.repository.GstRtspServer.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005939.python.hook-gi.repository.GstRtspServer.line5.comment or later) with exception for distributing the bootloader.
# 005940.python.hook-gi.repository.GstRtspServer.line6.comment
# 005941.python.hook-gi.repository.GstRtspServer.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005942.python.hook-gi.repository.GstRtspServer.line8.comment
# 005943.python.hook-gi.repository.GstRtspServer.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005944.python.hook-gi.repository.GstRtspServer.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstRtspServer', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
