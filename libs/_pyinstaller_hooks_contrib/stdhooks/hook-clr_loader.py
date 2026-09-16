# 012573.python.hook-clr_loader.line1.comment ------------------------------------------------------------------
# 012574.python.hook-clr_loader.line2.comment Copyright (c) 2022 PyInstaller Development Team.
# 012575.python.hook-clr_loader.line3.comment
# 012576.python.hook-clr_loader.line4.comment This file is distributed under the terms of the GNU General Public
# 012577.python.hook-clr_loader.line5.comment License (version 2.0 or later).
# 012578.python.hook-clr_loader.line6.comment
# 012579.python.hook-clr_loader.line7.comment The full license is available in LICENSE, distributed with
# 012580.python.hook-clr_loader.line8.comment this software.
# 012581.python.hook-clr_loader.line9.comment
# 012582.python.hook-clr_loader.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012583.python.hook-clr_loader.line11.comment ------------------------------------------------------------------

from PyInstaller.compat import is_win, is_cygwin
from PyInstaller.utils.hooks import collect_dynamic_libs

# 012584.python.hook-clr_loader.line16.comment The clr-loader is used by pythonnet 3.x to load CLR (.NET) runtime.
# 012585.python.hook-clr_loader.line17.comment On Windows, the default runtime is the .NET Framework, and its corresponding
# 012586.python.hook-clr_loader.line18.comment loader requires DLLs from clr_loader\ffi\dlls to be collected. This runtime
# 012587.python.hook-clr_loader.line19.comment is supported only on Windows, so we do not have to worry about it on other
# 012588.python.hook-clr_loader.line20.comment OSes (where Mono or .NET Core are supported).
if is_win or is_cygwin:
    binaries = collect_dynamic_libs("clr_loader")
