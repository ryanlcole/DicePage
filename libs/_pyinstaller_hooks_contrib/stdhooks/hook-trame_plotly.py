# 017920.python.hook-trame_plotly.line1.comment ------------------------------------------------------------------
# 017921.python.hook-trame_plotly.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017922.python.hook-trame_plotly.line3.comment
# 017923.python.hook-trame_plotly.line4.comment This file is distributed under the terms of the GNU General Public
# 017924.python.hook-trame_plotly.line5.comment License (version 2.0 or later).
# 017925.python.hook-trame_plotly.line6.comment
# 017926.python.hook-trame_plotly.line7.comment The full license is available in LICENSE, distributed with
# 017927.python.hook-trame_plotly.line8.comment this software.
# 017928.python.hook-trame_plotly.line9.comment
# 017929.python.hook-trame_plotly.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017930.python.hook-trame_plotly.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("trame_plotly", subdir="module")
