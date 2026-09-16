# 005845.python.hook-gi.repository.GstGLX11.line1.comment -----------------------------------------------------------------------------
# 005846.python.hook-gi.repository.GstGLX11.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005847.python.hook-gi.repository.GstGLX11.line3.comment
# 005848.python.hook-gi.repository.GstGLX11.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005849.python.hook-gi.repository.GstGLX11.line5.comment or later) with exception for distributing the bootloader.
# 005850.python.hook-gi.repository.GstGLX11.line6.comment
# 005851.python.hook-gi.repository.GstGLX11.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005852.python.hook-gi.repository.GstGLX11.line8.comment
# 005853.python.hook-gi.repository.GstGLX11.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005854.python.hook-gi.repository.GstGLX11.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks.gi import GiModuleInfo

module_info = GiModuleInfo('GstGLX11', '1.0')
if module_info.available:
    binaries, datas, hiddenimports = module_info.collect_typelib_data()
