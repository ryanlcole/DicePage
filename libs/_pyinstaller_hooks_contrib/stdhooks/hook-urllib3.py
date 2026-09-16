# 018242.python.hook-urllib3.line1.comment ------------------------------------------------------------------
# 018243.python.hook-urllib3.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 018244.python.hook-urllib3.line3.comment
# 018245.python.hook-urllib3.line4.comment This file is distributed under the terms of the GNU General Public
# 018246.python.hook-urllib3.line5.comment License (version 2.0 or later).
# 018247.python.hook-urllib3.line6.comment
# 018248.python.hook-urllib3.line7.comment The full license is available in LICENSE, distributed with
# 018249.python.hook-urllib3.line8.comment this software.
# 018250.python.hook-urllib3.line9.comment
# 018251.python.hook-urllib3.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018252.python.hook-urllib3.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules, is_module_satisfies

# 018253.python.hook-urllib3.line15.comment If this is `urllib3` from `urllib3-future`, collect submodules in order to avoid missing modules due to indirect
# 018254.python.hook-urllib3.line16.comment imports. With `urllib3` from "classic" `urllib3`, this does not seem to be necessary.
if is_module_satisfies("urllib3-future"):
    hiddenimports = collect_submodules("urllib3")
