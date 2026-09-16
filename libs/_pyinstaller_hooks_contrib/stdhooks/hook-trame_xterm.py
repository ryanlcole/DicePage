# 018063.python.hook-trame_xterm.line1.comment ------------------------------------------------------------------
# 018064.python.hook-trame_xterm.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 018065.python.hook-trame_xterm.line3.comment
# 018066.python.hook-trame_xterm.line4.comment This file is distributed under the terms of the GNU General Public
# 018067.python.hook-trame_xterm.line5.comment License (version 2.0 or later).
# 018068.python.hook-trame_xterm.line6.comment
# 018069.python.hook-trame_xterm.line7.comment The full license is available in LICENSE, distributed with
# 018070.python.hook-trame_xterm.line8.comment this software.
# 018071.python.hook-trame_xterm.line9.comment
# 018072.python.hook-trame_xterm.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018073.python.hook-trame_xterm.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("trame_xterm", subdir="module")
