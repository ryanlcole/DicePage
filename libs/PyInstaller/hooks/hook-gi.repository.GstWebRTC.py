# 006015.python.hook-gi.repository.GstWebRTC.line1.comment -----------------------------------------------------------------------------
# 006016.python.hook-gi.repository.GstWebRTC.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 006017.python.hook-gi.repository.GstWebRTC.line3.comment
# 006018.python.hook-gi.repository.GstWebRTC.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006019.python.hook-gi.repository.GstWebRTC.line5.comment or later) with exception for distributing the bootloader.
# 006020.python.hook-gi.repository.GstWebRTC.line6.comment
# 006021.python.hook-gi.repository.GstWebRTC.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006022.python.hook-gi.repository.GstWebRTC.line8.comment
# 006023.python.hook-gi.repository.GstWebRTC.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006024.python.hook-gi.repository.GstWebRTC.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstWebRTC', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
