# 017843.python.hook-trame_grid.line1.comment ------------------------------------------------------------------
# 017844.python.hook-trame_grid.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017845.python.hook-trame_grid.line3.comment
# 017846.python.hook-trame_grid.line4.comment This file is distributed under the terms of the GNU General Public
# 017847.python.hook-trame_grid.line5.comment License (version 2.0 or later).
# 017848.python.hook-trame_grid.line6.comment
# 017849.python.hook-trame_grid.line7.comment The full license is available in LICENSE, distributed with
# 017850.python.hook-trame_grid.line8.comment this software.
# 017851.python.hook-trame_grid.line9.comment
# 017852.python.hook-trame_grid.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017853.python.hook-trame_grid.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = [*collect_data_files("trame_grid", subdir="module")]
