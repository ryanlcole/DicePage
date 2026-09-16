# 017604.python.hook-toga_cocoa.line1.comment ------------------------------------------------------------------
# 017605.python.hook-toga_cocoa.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017606.python.hook-toga_cocoa.line3.comment
# 017607.python.hook-toga_cocoa.line4.comment This file is distributed under the terms of the GNU General Public
# 017608.python.hook-toga_cocoa.line5.comment License (version 2.0 or later).
# 017609.python.hook-toga_cocoa.line6.comment
# 017610.python.hook-toga_cocoa.line7.comment The full license is available in LICENSE, distributed with
# 017611.python.hook-toga_cocoa.line8.comment this software.
# 017612.python.hook-toga_cocoa.line9.comment
# 017613.python.hook-toga_cocoa.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017614.python.hook-toga_cocoa.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, copy_metadata

# 017615.python.hook-toga_cocoa.line15.comment Collect icons from `resources`.
datas = collect_data_files('toga_cocoa')

# 017616.python.hook-toga_cocoa.line18.comment Collect metadata so that the backend can be discovered via `toga.backends` entry-point.
datas += copy_metadata("toga-cocoa")
