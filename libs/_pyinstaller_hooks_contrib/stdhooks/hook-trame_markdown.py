# 017887.python.hook-trame_markdown.line1.comment ------------------------------------------------------------------
# 017888.python.hook-trame_markdown.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017889.python.hook-trame_markdown.line3.comment
# 017890.python.hook-trame_markdown.line4.comment This file is distributed under the terms of the GNU General Public
# 017891.python.hook-trame_markdown.line5.comment License (version 2.0 or later).
# 017892.python.hook-trame_markdown.line6.comment
# 017893.python.hook-trame_markdown.line7.comment The full license is available in LICENSE, distributed with
# 017894.python.hook-trame_markdown.line8.comment this software.
# 017895.python.hook-trame_markdown.line9.comment
# 017896.python.hook-trame_markdown.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017897.python.hook-trame_markdown.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = [*collect_data_files("trame_markdown", subdir="module")]
