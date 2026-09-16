# 015488.python.hook-py.line1.comment ------------------------------------------------------------------
# 015489.python.hook-py.line2.comment Copyright (c) 2022 PyInstaller Development Team.
# 015490.python.hook-py.line3.comment
# 015491.python.hook-py.line4.comment This file is distributed under the terms of the GNU General Public
# 015492.python.hook-py.line5.comment License (version 2.0 or later).
# 015493.python.hook-py.line6.comment
# 015494.python.hook-py.line7.comment The full license is available in LICENSE, distributed with
# 015495.python.hook-py.line8.comment this software.
# 015496.python.hook-py.line9.comment
# 015497.python.hook-py.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015498.python.hook-py.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("py._path")
