# 005765.python.hook-gi.repository.GstBadAudio.line1.comment -----------------------------------------------------------------------------
# 005766.python.hook-gi.repository.GstBadAudio.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005767.python.hook-gi.repository.GstBadAudio.line3.comment
# 005768.python.hook-gi.repository.GstBadAudio.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005769.python.hook-gi.repository.GstBadAudio.line5.comment or later) with exception for distributing the bootloader.
# 005770.python.hook-gi.repository.GstBadAudio.line6.comment
# 005771.python.hook-gi.repository.GstBadAudio.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005772.python.hook-gi.repository.GstBadAudio.line8.comment
# 005773.python.hook-gi.repository.GstBadAudio.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005774.python.hook-gi.repository.GstBadAudio.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstBadAudio', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
