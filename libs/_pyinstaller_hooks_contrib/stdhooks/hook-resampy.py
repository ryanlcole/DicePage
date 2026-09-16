# 016476.python.hook-resampy.line1.comment ------------------------------------------------------------------
# 016477.python.hook-resampy.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016478.python.hook-resampy.line3.comment
# 016479.python.hook-resampy.line4.comment This file is distributed under the terms of the GNU General Public
# 016480.python.hook-resampy.line5.comment License (version 2.0 or later).
# 016481.python.hook-resampy.line6.comment
# 016482.python.hook-resampy.line7.comment The full license is available in LICENSE, distributed with
# 016483.python.hook-resampy.line8.comment this software.
# 016484.python.hook-resampy.line9.comment
# 016485.python.hook-resampy.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016486.python.hook-resampy.line11.comment ------------------------------------------------------------------

# 016487.python.hook-resampy.line13.comment Hook for resampy
from PyInstaller.utils.hooks import collect_data_files

# 016488.python.hook-resampy.line16.comment resampy has two data files that need to be included.
datas = collect_data_files('resampy', False)
