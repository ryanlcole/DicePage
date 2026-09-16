# 017062.python.hook-sklearn.metrics.pairwise.line1.comment ------------------------------------------------------------------
# 017063.python.hook-sklearn.metrics.pairwise.line2.comment Copyright (c) 2022 PyInstaller Development Team.
# 017064.python.hook-sklearn.metrics.pairwise.line3.comment
# 017065.python.hook-sklearn.metrics.pairwise.line4.comment This file is distributed under the terms of the GNU General Public
# 017066.python.hook-sklearn.metrics.pairwise.line5.comment License (version 2.0 or later).
# 017067.python.hook-sklearn.metrics.pairwise.line6.comment
# 017068.python.hook-sklearn.metrics.pairwise.line7.comment The full license is available in LICENSE, distributed with
# 017069.python.hook-sklearn.metrics.pairwise.line8.comment this software.
# 017070.python.hook-sklearn.metrics.pairwise.line9.comment
# 017071.python.hook-sklearn.metrics.pairwise.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017072.python.hook-sklearn.metrics.pairwise.line11.comment ------------------------------------------------------------------

# 017073.python.hook-sklearn.metrics.pairwise.line13.comment Required by scikit-learn 1.1.0
from PyInstaller.utils.hooks import is_module_satisfies

if is_module_satisfies("scikit-learn >= 1.1.0"):
    hiddenimports = [
        'sklearn.utils._heap',
        'sklearn.utils._sorting',
        'sklearn.utils._vector_sentinel',
    ]
