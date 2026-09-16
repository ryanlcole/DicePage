# 005825.python.hook-gi.repository.GstGLEGL.line1.comment -----------------------------------------------------------------------------
# 005826.python.hook-gi.repository.GstGLEGL.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005827.python.hook-gi.repository.GstGLEGL.line3.comment
# 005828.python.hook-gi.repository.GstGLEGL.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005829.python.hook-gi.repository.GstGLEGL.line5.comment or later) with exception for distributing the bootloader.
# 005830.python.hook-gi.repository.GstGLEGL.line6.comment
# 005831.python.hook-gi.repository.GstGLEGL.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005832.python.hook-gi.repository.GstGLEGL.line8.comment
# 005833.python.hook-gi.repository.GstGLEGL.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005834.python.hook-gi.repository.GstGLEGL.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstGLEGL', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
