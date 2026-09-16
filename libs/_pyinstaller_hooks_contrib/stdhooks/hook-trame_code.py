# 017788.python.hook-trame_code.line1.comment ------------------------------------------------------------------
# 017789.python.hook-trame_code.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017790.python.hook-trame_code.line3.comment
# 017791.python.hook-trame_code.line4.comment This file is distributed under the terms of the GNU General Public
# 017792.python.hook-trame_code.line5.comment License (version 2.0 or later).
# 017793.python.hook-trame_code.line6.comment
# 017794.python.hook-trame_code.line7.comment The full license is available in LICENSE, distributed with
# 017795.python.hook-trame_code.line8.comment this software.
# 017796.python.hook-trame_code.line9.comment
# 017797.python.hook-trame_code.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017798.python.hook-trame_code.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = [*collect_data_files("trame_code", subdir="module")]
