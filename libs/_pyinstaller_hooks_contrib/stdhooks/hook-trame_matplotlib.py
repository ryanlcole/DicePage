# 017898.python.hook-trame_matplotlib.line1.comment ------------------------------------------------------------------
# 017899.python.hook-trame_matplotlib.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017900.python.hook-trame_matplotlib.line3.comment
# 017901.python.hook-trame_matplotlib.line4.comment This file is distributed under the terms of the GNU General Public
# 017902.python.hook-trame_matplotlib.line5.comment License (version 2.0 or later).
# 017903.python.hook-trame_matplotlib.line6.comment
# 017904.python.hook-trame_matplotlib.line7.comment The full license is available in LICENSE, distributed with
# 017905.python.hook-trame_matplotlib.line8.comment this software.
# 017906.python.hook-trame_matplotlib.line9.comment
# 017907.python.hook-trame_matplotlib.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017908.python.hook-trame_matplotlib.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = [*collect_data_files("trame_matplotlib", subdir="module")]
