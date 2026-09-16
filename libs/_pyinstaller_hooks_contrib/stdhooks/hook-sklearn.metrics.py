# 017074.python.hook-sklearn.metrics.line1.comment ------------------------------------------------------------------
# 017075.python.hook-sklearn.metrics.line2.comment Copyright (c) 2022 PyInstaller Development Team.
# 017076.python.hook-sklearn.metrics.line3.comment
# 017077.python.hook-sklearn.metrics.line4.comment This file is distributed under the terms of the GNU General Public
# 017078.python.hook-sklearn.metrics.line5.comment License (version 2.0 or later).
# 017079.python.hook-sklearn.metrics.line6.comment
# 017080.python.hook-sklearn.metrics.line7.comment The full license is available in LICENSE, distributed with
# 017081.python.hook-sklearn.metrics.line8.comment this software.
# 017082.python.hook-sklearn.metrics.line9.comment
# 017083.python.hook-sklearn.metrics.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017084.python.hook-sklearn.metrics.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies, collect_submodules

hiddenimports = []

# 017085.python.hook-sklearn.metrics.line17.comment Required by scikit-learn 1.0.0
if is_module_satisfies("scikit-learn >= 1.0.0"):
    hiddenimports += [
        'sklearn.utils._typedefs',
    ]

# 017086.python.hook-sklearn.metrics.line23.comment Required by scikit-learn 1.2.0
if is_module_satisfies("scikit-learn >= 1.2.0"):
    hiddenimports += collect_submodules("sklearn.metrics._pairwise_distances_reduction")
