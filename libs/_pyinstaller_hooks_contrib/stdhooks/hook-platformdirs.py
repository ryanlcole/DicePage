# 015357.python.hook-platformdirs.line1.comment ------------------------------------------------------------------
# 015358.python.hook-platformdirs.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 015359.python.hook-platformdirs.line3.comment
# 015360.python.hook-platformdirs.line4.comment This file is distributed under the terms of the GNU General Public
# 015361.python.hook-platformdirs.line5.comment License (version 2.0 or later).
# 015362.python.hook-platformdirs.line6.comment
# 015363.python.hook-platformdirs.line7.comment The full license is available in LICENSE, distributed with
# 015364.python.hook-platformdirs.line8.comment this software.
# 015365.python.hook-platformdirs.line9.comment
# 015366.python.hook-platformdirs.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015367.python.hook-platformdirs.line11.comment ------------------------------------------------------------------

from PyInstaller.compat import is_darwin, is_win

modules = ["platformdirs"]

# 015368.python.hook-platformdirs.line17.comment platfromdirs contains dynamically loaded per-platform submodules.
if is_darwin:
    modules.append("platformdirs.macos")
elif is_win:
    modules.append("platformdirs.windows")
else:
    # 015369.python.hook-platformdirs.line23.comment default to unix for all other platforms
    # 015370.python.hook-platformdirs.line24.comment this includes unix, cygwin, and msys2
    modules.append("platformdirs.unix")

hiddenimports = modules
