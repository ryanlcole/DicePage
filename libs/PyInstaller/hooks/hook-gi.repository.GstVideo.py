# 005975.python.hook-gi.repository.GstVideo.line1.comment -----------------------------------------------------------------------------
# 005976.python.hook-gi.repository.GstVideo.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005977.python.hook-gi.repository.GstVideo.line3.comment
# 005978.python.hook-gi.repository.GstVideo.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005979.python.hook-gi.repository.GstVideo.line5.comment or later) with exception for distributing the bootloader.
# 005980.python.hook-gi.repository.GstVideo.line6.comment
# 005981.python.hook-gi.repository.GstVideo.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005982.python.hook-gi.repository.GstVideo.line8.comment
# 005983.python.hook-gi.repository.GstVideo.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005984.python.hook-gi.repository.GstVideo.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstVideo', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
