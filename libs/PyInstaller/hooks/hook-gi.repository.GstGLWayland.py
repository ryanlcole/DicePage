# 005835.python.hook-gi.repository.GstGLWayland.line1.comment -----------------------------------------------------------------------------
# 005836.python.hook-gi.repository.GstGLWayland.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005837.python.hook-gi.repository.GstGLWayland.line3.comment
# 005838.python.hook-gi.repository.GstGLWayland.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005839.python.hook-gi.repository.GstGLWayland.line5.comment or later) with exception for distributing the bootloader.
# 005840.python.hook-gi.repository.GstGLWayland.line6.comment
# 005841.python.hook-gi.repository.GstGLWayland.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005842.python.hook-gi.repository.GstGLWayland.line8.comment
# 005843.python.hook-gi.repository.GstGLWayland.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005844.python.hook-gi.repository.GstGLWayland.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstGLWayland', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
