# 013627.python.hook-gooey.line1.comment ------------------------------------------------------------------
# 013628.python.hook-gooey.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 013629.python.hook-gooey.line3.comment
# 013630.python.hook-gooey.line4.comment This file is distributed under the terms of the GNU General Public
# 013631.python.hook-gooey.line5.comment License (version 2.0 or later).
# 013632.python.hook-gooey.line6.comment
# 013633.python.hook-gooey.line7.comment The full license is available in LICENSE, distributed with
# 013634.python.hook-gooey.line8.comment this software.
# 013635.python.hook-gooey.line9.comment
# 013636.python.hook-gooey.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013637.python.hook-gooey.line11.comment ------------------------------------------------------------------
"""
Gooey GUI carries some language and images for it's UI to function.
"""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('gooey')
