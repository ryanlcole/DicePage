# 017104.python.hook-sklearn.line1.comment ------------------------------------------------------------------
# 017105.python.hook-sklearn.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 017106.python.hook-sklearn.line3.comment
# 017107.python.hook-sklearn.line4.comment This file is distributed under the terms of the GNU General Public
# 017108.python.hook-sklearn.line5.comment License (version 2.0 or later).
# 017109.python.hook-sklearn.line6.comment
# 017110.python.hook-sklearn.line7.comment The full license is available in LICENSE, distributed with
# 017111.python.hook-sklearn.line8.comment this software.
# 017112.python.hook-sklearn.line9.comment
# 017113.python.hook-sklearn.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017114.python.hook-sklearn.line11.comment ------------------------------------------------------------------

# 017115.python.hook-sklearn.line13.comment Tested on Windows 10 64bit with python 3.7.1

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('sklearn')
