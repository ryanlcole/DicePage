# 017931.python.hook-trame_pvui.line1.comment ------------------------------------------------------------------
# 017932.python.hook-trame_pvui.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017933.python.hook-trame_pvui.line3.comment
# 017934.python.hook-trame_pvui.line4.comment This file is distributed under the terms of the GNU General Public
# 017935.python.hook-trame_pvui.line5.comment License (version 2.0 or later).
# 017936.python.hook-trame_pvui.line6.comment
# 017937.python.hook-trame_pvui.line7.comment The full license is available in LICENSE, distributed with
# 017938.python.hook-trame_pvui.line8.comment this software.
# 017939.python.hook-trame_pvui.line9.comment
# 017940.python.hook-trame_pvui.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017941.python.hook-trame_pvui.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("trame_pvui", subdir="module")
