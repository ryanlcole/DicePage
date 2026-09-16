# 017810.python.hook-trame_datagrid.line1.comment ------------------------------------------------------------------
# 017811.python.hook-trame_datagrid.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017812.python.hook-trame_datagrid.line3.comment
# 017813.python.hook-trame_datagrid.line4.comment This file is distributed under the terms of the GNU General Public
# 017814.python.hook-trame_datagrid.line5.comment License (version 2.0 or later).
# 017815.python.hook-trame_datagrid.line6.comment
# 017816.python.hook-trame_datagrid.line7.comment The full license is available in LICENSE, distributed with
# 017817.python.hook-trame_datagrid.line8.comment this software.
# 017818.python.hook-trame_datagrid.line9.comment
# 017819.python.hook-trame_datagrid.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017820.python.hook-trame_datagrid.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("trame_datagrid", subdir="module")
