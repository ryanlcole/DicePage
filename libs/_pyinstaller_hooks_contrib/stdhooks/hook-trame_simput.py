# 017975.python.hook-trame_simput.line1.comment ------------------------------------------------------------------
# 017976.python.hook-trame_simput.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017977.python.hook-trame_simput.line3.comment
# 017978.python.hook-trame_simput.line4.comment This file is distributed under the terms of the GNU General Public
# 017979.python.hook-trame_simput.line5.comment License (version 2.0 or later).
# 017980.python.hook-trame_simput.line6.comment
# 017981.python.hook-trame_simput.line7.comment The full license is available in LICENSE, distributed with
# 017982.python.hook-trame_simput.line8.comment this software.
# 017983.python.hook-trame_simput.line9.comment
# 017984.python.hook-trame_simput.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017985.python.hook-trame_simput.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("trame_simput", subdir="module")
