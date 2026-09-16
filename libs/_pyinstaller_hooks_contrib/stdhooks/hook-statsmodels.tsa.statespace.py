# 017278.python.hook-statsmodels.tsa.statespace.line1.comment ------------------------------------------------------------------
# 017279.python.hook-statsmodels.tsa.statespace.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 017280.python.hook-statsmodels.tsa.statespace.line3.comment
# 017281.python.hook-statsmodels.tsa.statespace.line4.comment This file is distributed under the terms of the GNU General Public
# 017282.python.hook-statsmodels.tsa.statespace.line5.comment License (version 2.0 or later).
# 017283.python.hook-statsmodels.tsa.statespace.line6.comment
# 017284.python.hook-statsmodels.tsa.statespace.line7.comment The full license is available in LICENSE, distributed with
# 017285.python.hook-statsmodels.tsa.statespace.line8.comment this software.
# 017286.python.hook-statsmodels.tsa.statespace.line9.comment
# 017287.python.hook-statsmodels.tsa.statespace.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017288.python.hook-statsmodels.tsa.statespace.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('statsmodels.tsa.statespace._filters') \
    + collect_submodules('statsmodels.tsa.statespace._smoothers')
