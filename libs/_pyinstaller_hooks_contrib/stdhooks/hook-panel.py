# 015197.python.hook-panel.line1.comment ------------------------------------------------------------------
# 015198.python.hook-panel.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 015199.python.hook-panel.line3.comment
# 015200.python.hook-panel.line4.comment This file is distributed under the terms of the GNU General Public
# 015201.python.hook-panel.line5.comment License (version 2.0 or later).
# 015202.python.hook-panel.line6.comment
# 015203.python.hook-panel.line7.comment The full license is available in LICENSE, distributed with
# 015204.python.hook-panel.line8.comment this software.
# 015205.python.hook-panel.line9.comment
# 015206.python.hook-panel.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015207.python.hook-panel.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = collect_data_files("panel")

# 015208.python.hook-panel.line17.comment Some models are lazy-loaded on runtime, so we need to collect them
hiddenimports = collect_submodules("panel.models")
