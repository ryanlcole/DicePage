# 017821.python.hook-trame_deckgl.line1.comment ------------------------------------------------------------------
# 017822.python.hook-trame_deckgl.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017823.python.hook-trame_deckgl.line3.comment
# 017824.python.hook-trame_deckgl.line4.comment This file is distributed under the terms of the GNU General Public
# 017825.python.hook-trame_deckgl.line5.comment License (version 2.0 or later).
# 017826.python.hook-trame_deckgl.line6.comment
# 017827.python.hook-trame_deckgl.line7.comment The full license is available in LICENSE, distributed with
# 017828.python.hook-trame_deckgl.line8.comment this software.
# 017829.python.hook-trame_deckgl.line9.comment
# 017830.python.hook-trame_deckgl.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017831.python.hook-trame_deckgl.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("trame_deckgl", subdir="module")
