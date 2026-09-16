# 018008.python.hook-trame_vega.line1.comment ------------------------------------------------------------------
# 018009.python.hook-trame_vega.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 018010.python.hook-trame_vega.line3.comment
# 018011.python.hook-trame_vega.line4.comment This file is distributed under the terms of the GNU General Public
# 018012.python.hook-trame_vega.line5.comment License (version 2.0 or later).
# 018013.python.hook-trame_vega.line6.comment
# 018014.python.hook-trame_vega.line7.comment The full license is available in LICENSE, distributed with
# 018015.python.hook-trame_vega.line8.comment this software.
# 018016.python.hook-trame_vega.line9.comment
# 018017.python.hook-trame_vega.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018018.python.hook-trame_vega.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("trame_vega", subdir="module")
