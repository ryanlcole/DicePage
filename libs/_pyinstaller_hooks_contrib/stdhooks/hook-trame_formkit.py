# 017832.python.hook-trame_formkit.line1.comment ------------------------------------------------------------------
# 017833.python.hook-trame_formkit.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017834.python.hook-trame_formkit.line3.comment
# 017835.python.hook-trame_formkit.line4.comment This file is distributed under the terms of the GNU General Public
# 017836.python.hook-trame_formkit.line5.comment License (version 2.0 or later).
# 017837.python.hook-trame_formkit.line6.comment
# 017838.python.hook-trame_formkit.line7.comment The full license is available in LICENSE, distributed with
# 017839.python.hook-trame_formkit.line8.comment this software.
# 017840.python.hook-trame_formkit.line9.comment
# 017841.python.hook-trame_formkit.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017842.python.hook-trame_formkit.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = [*collect_data_files("trame_formkit", subdir="module")]
