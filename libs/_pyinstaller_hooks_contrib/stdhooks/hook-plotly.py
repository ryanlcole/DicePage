# 015371.python.hook-plotly.line1.comment ------------------------------------------------------------------
# 015372.python.hook-plotly.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 015373.python.hook-plotly.line3.comment
# 015374.python.hook-plotly.line4.comment This file is distributed under the terms of the GNU General Public
# 015375.python.hook-plotly.line5.comment License (version 2.0 or later).
# 015376.python.hook-plotly.line6.comment
# 015377.python.hook-plotly.line7.comment The full license is available in LICENSE, distributed with
# 015378.python.hook-plotly.line8.comment this software.
# 015379.python.hook-plotly.line9.comment
# 015380.python.hook-plotly.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015381.python.hook-plotly.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_submodules

datas = collect_data_files('plotly', includes=['package_data/**/*.*', 'validators/**/*.*'])
hiddenimports = collect_submodules('plotly.validators') + ['pandas', 'cmath']
