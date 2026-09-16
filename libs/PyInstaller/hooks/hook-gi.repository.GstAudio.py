# 005755.python.hook-gi.repository.GstAudio.line1.comment -----------------------------------------------------------------------------
# 005756.python.hook-gi.repository.GstAudio.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005757.python.hook-gi.repository.GstAudio.line3.comment
# 005758.python.hook-gi.repository.GstAudio.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005759.python.hook-gi.repository.GstAudio.line5.comment or later) with exception for distributing the bootloader.
# 005760.python.hook-gi.repository.GstAudio.line6.comment
# 005761.python.hook-gi.repository.GstAudio.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005762.python.hook-gi.repository.GstAudio.line8.comment
# 005763.python.hook-gi.repository.GstAudio.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005764.python.hook-gi.repository.GstAudio.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstAudio', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
