# 017964.python.hook-trame_router.line1.comment ------------------------------------------------------------------
# 017965.python.hook-trame_router.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017966.python.hook-trame_router.line3.comment
# 017967.python.hook-trame_router.line4.comment This file is distributed under the terms of the GNU General Public
# 017968.python.hook-trame_router.line5.comment License (version 2.0 or later).
# 017969.python.hook-trame_router.line6.comment
# 017970.python.hook-trame_router.line7.comment The full license is available in LICENSE, distributed with
# 017971.python.hook-trame_router.line8.comment this software.
# 017972.python.hook-trame_router.line9.comment
# 017973.python.hook-trame_router.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017974.python.hook-trame_router.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("trame_router", subdir="module")
