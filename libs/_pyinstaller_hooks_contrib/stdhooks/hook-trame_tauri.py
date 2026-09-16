# 017986.python.hook-trame_tauri.line1.comment ------------------------------------------------------------------
# 017987.python.hook-trame_tauri.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017988.python.hook-trame_tauri.line3.comment
# 017989.python.hook-trame_tauri.line4.comment This file is distributed under the terms of the GNU General Public
# 017990.python.hook-trame_tauri.line5.comment License (version 2.0 or later).
# 017991.python.hook-trame_tauri.line6.comment
# 017992.python.hook-trame_tauri.line7.comment The full license is available in LICENSE, distributed with
# 017993.python.hook-trame_tauri.line8.comment this software.
# 017994.python.hook-trame_tauri.line9.comment
# 017995.python.hook-trame_tauri.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017996.python.hook-trame_tauri.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("trame_tauri", subdir="module")
