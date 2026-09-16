# 012589.python.hook-cmocean.line1.comment ------------------------------------------------------------------
# 012590.python.hook-cmocean.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 012591.python.hook-cmocean.line3.comment
# 012592.python.hook-cmocean.line4.comment This file is distributed under the terms of the GNU General Public
# 012593.python.hook-cmocean.line5.comment License (version 2.0 or later).
# 012594.python.hook-cmocean.line6.comment
# 012595.python.hook-cmocean.line7.comment The full license is available in LICENSE, distributed with
# 012596.python.hook-cmocean.line8.comment this software.
# 012597.python.hook-cmocean.line9.comment
# 012598.python.hook-cmocean.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012599.python.hook-cmocean.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("cmocean", subdir="rgb")
