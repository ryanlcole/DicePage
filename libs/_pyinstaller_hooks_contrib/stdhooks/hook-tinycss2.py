# 017525.python.hook-tinycss2.line1.comment ------------------------------------------------------------------
# 017526.python.hook-tinycss2.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 017527.python.hook-tinycss2.line3.comment
# 017528.python.hook-tinycss2.line4.comment This file is distributed under the terms of the GNU General Public
# 017529.python.hook-tinycss2.line5.comment License (version 2.0 or later).
# 017530.python.hook-tinycss2.line6.comment
# 017531.python.hook-tinycss2.line7.comment The full license is available in LICENSE, distributed with
# 017532.python.hook-tinycss2.line8.comment this software.
# 017533.python.hook-tinycss2.line9.comment
# 017534.python.hook-tinycss2.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017535.python.hook-tinycss2.line11.comment ------------------------------------------------------------------
"""
Hook for tinycss2. tinycss2 is a low-level CSS parser and generator.
https://github.com/Kozea/tinycss2
"""
from PyInstaller.utils.hooks import collect_data_files


# 017536.python.hook-tinycss2.line19.comment Hook no longer required for tinycss2 >= 1.0.0
def hook(hook_api):
    hook_api.add_datas(collect_data_files(hook_api.__name__))
