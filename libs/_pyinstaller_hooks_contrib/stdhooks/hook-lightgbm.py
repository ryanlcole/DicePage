# 014299.python.hook-lightgbm.line1.comment ------------------------------------------------------------------
# 014300.python.hook-lightgbm.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014301.python.hook-lightgbm.line3.comment
# 014302.python.hook-lightgbm.line4.comment This file is distributed under the terms of the GNU General Public
# 014303.python.hook-lightgbm.line5.comment License (version 2.0 or later).
# 014304.python.hook-lightgbm.line6.comment
# 014305.python.hook-lightgbm.line7.comment The full license is available in LICENSE, distributed with
# 014306.python.hook-lightgbm.line8.comment this software.
# 014307.python.hook-lightgbm.line9.comment
# 014308.python.hook-lightgbm.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014309.python.hook-lightgbm.line11.comment ------------------------------------------------------------------
# 014310.python.hook-lightgbm.line12.comment
# 014311.python.hook-lightgbm.line13.comment A fast, distributed, high performance gradient boosting
# 014312.python.hook-lightgbm.line14.comment (GBT, GBDT, GBRT, GBM or MART) framework based on decision
# 014313.python.hook-lightgbm.line15.comment tree algorithms, used for ranking, classification and
# 014314.python.hook-lightgbm.line16.comment many other machine learning tasks.
# 014315.python.hook-lightgbm.line17.comment
# 014316.python.hook-lightgbm.line18.comment https://github.com/microsoft/LightGBM
# 014317.python.hook-lightgbm.line19.comment
# 014318.python.hook-lightgbm.line20.comment Tested with:
# 014319.python.hook-lightgbm.line21.comment Tested on Windows 10 & macOS 10.14 with Python 3.7.5

from PyInstaller.utils.hooks import collect_dynamic_libs

binaries = collect_dynamic_libs('lightgbm')
binaries += collect_dynamic_libs('sklearn')
binaries += collect_dynamic_libs('scipy')
