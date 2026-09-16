# 017034.python.hook-sklearn.linear_model.line1.comment ------------------------------------------------------------------
# 017035.python.hook-sklearn.linear_model.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 017036.python.hook-sklearn.linear_model.line3.comment
# 017037.python.hook-sklearn.linear_model.line4.comment This file is distributed under the terms of the GNU General Public
# 017038.python.hook-sklearn.linear_model.line5.comment License (version 2.0 or later).
# 017039.python.hook-sklearn.linear_model.line6.comment
# 017040.python.hook-sklearn.linear_model.line7.comment The full license is available in LICENSE, distributed with
# 017041.python.hook-sklearn.linear_model.line8.comment this software.
# 017042.python.hook-sklearn.linear_model.line9.comment
# 017043.python.hook-sklearn.linear_model.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017044.python.hook-sklearn.linear_model.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies

# 017045.python.hook-sklearn.linear_model.line15.comment sklearn.linear_model in scikit-learn 0.24.x has a hidden import of
# 017046.python.hook-sklearn.linear_model.line16.comment sklearn.utils._weight_vector
if is_module_satisfies("scikit_learn >= 0.24"):
    hiddenimports = ['sklearn.utils._weight_vector', ]
