# 017799.python.hook-trame_components.line1.comment ------------------------------------------------------------------
# 017800.python.hook-trame_components.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017801.python.hook-trame_components.line3.comment
# 017802.python.hook-trame_components.line4.comment This file is distributed under the terms of the GNU General Public
# 017803.python.hook-trame_components.line5.comment License (version 2.0 or later).
# 017804.python.hook-trame_components.line6.comment
# 017805.python.hook-trame_components.line7.comment The full license is available in LICENSE, distributed with
# 017806.python.hook-trame_components.line8.comment this software.
# 017807.python.hook-trame_components.line9.comment
# 017808.python.hook-trame_components.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017809.python.hook-trame_components.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("trame_components", subdir="module")
