# 017777.python.hook-trame_client.line1.comment ------------------------------------------------------------------
# 017778.python.hook-trame_client.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017779.python.hook-trame_client.line3.comment
# 017780.python.hook-trame_client.line4.comment This file is distributed under the terms of the GNU General Public
# 017781.python.hook-trame_client.line5.comment License (version 2.0 or later).
# 017782.python.hook-trame_client.line6.comment
# 017783.python.hook-trame_client.line7.comment The full license is available in LICENSE, distributed with
# 017784.python.hook-trame_client.line8.comment this software.
# 017785.python.hook-trame_client.line9.comment
# 017786.python.hook-trame_client.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017787.python.hook-trame_client.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("trame_client", subdir="module")
