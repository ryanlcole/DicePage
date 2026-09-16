# 017047.python.hook-sklearn.metrics.cluster.line1.comment ------------------------------------------------------------------
# 017048.python.hook-sklearn.metrics.cluster.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 017049.python.hook-sklearn.metrics.cluster.line3.comment
# 017050.python.hook-sklearn.metrics.cluster.line4.comment This file is distributed under the terms of the GNU General Public
# 017051.python.hook-sklearn.metrics.cluster.line5.comment License (version 2.0 or later).
# 017052.python.hook-sklearn.metrics.cluster.line6.comment
# 017053.python.hook-sklearn.metrics.cluster.line7.comment The full license is available in LICENSE, distributed with
# 017054.python.hook-sklearn.metrics.cluster.line8.comment this software.
# 017055.python.hook-sklearn.metrics.cluster.line9.comment
# 017056.python.hook-sklearn.metrics.cluster.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017057.python.hook-sklearn.metrics.cluster.line11.comment ------------------------------------------------------------------

# 017058.python.hook-sklearn.metrics.cluster.line13.comment Required by scikit-learn 0.21
from PyInstaller.utils.hooks import is_module_satisfies

if is_module_satisfies("scikit-learn < 0.22"):
    hiddenimports = [
        'sklearn.utils.lgamma',
        'sklearn.utils.weight_vector'
    ]
else:
    # 017059.python.hook-sklearn.metrics.cluster.line22.comment lgamma was removed and weight_vector privatised in 0.22.
    # 017060.python.hook-sklearn.metrics.cluster.line23.comment https://github.com/scikit-learn/scikit-learn/commit/58be9a671b0b8fcb4b75f4ae99f4469ca33a2158#diff-dbca16040fd2b85a499ba59833b37f1785c58e52d2e89ce5cdfc7fff164bd5f3
    # 017061.python.hook-sklearn.metrics.cluster.line24.comment https://github.com/scikit-learn/scikit-learn/commit/150e82b52bf28c88c5a8b1a10f9777d0452b3ef2
    hiddenimports = [
        'sklearn.utils._weight_vector'
    ]
