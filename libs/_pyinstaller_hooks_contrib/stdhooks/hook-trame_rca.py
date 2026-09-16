# 017953.python.hook-trame_rca.line1.comment ------------------------------------------------------------------
# 017954.python.hook-trame_rca.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017955.python.hook-trame_rca.line3.comment
# 017956.python.hook-trame_rca.line4.comment This file is distributed under the terms of the GNU General Public
# 017957.python.hook-trame_rca.line5.comment License (version 2.0 or later).
# 017958.python.hook-trame_rca.line6.comment
# 017959.python.hook-trame_rca.line7.comment The full license is available in LICENSE, distributed with
# 017960.python.hook-trame_rca.line8.comment this software.
# 017961.python.hook-trame_rca.line9.comment
# 017962.python.hook-trame_rca.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017963.python.hook-trame_rca.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("trame_rca", subdir="module")
