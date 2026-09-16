# 017087.python.hook-sklearn.neighbors.line1.comment ------------------------------------------------------------------
# 017088.python.hook-sklearn.neighbors.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 017089.python.hook-sklearn.neighbors.line3.comment
# 017090.python.hook-sklearn.neighbors.line4.comment This file is distributed under the terms of the GNU General Public
# 017091.python.hook-sklearn.neighbors.line5.comment License (version 2.0 or later).
# 017092.python.hook-sklearn.neighbors.line6.comment
# 017093.python.hook-sklearn.neighbors.line7.comment The full license is available in LICENSE, distributed with
# 017094.python.hook-sklearn.neighbors.line8.comment this software.
# 017095.python.hook-sklearn.neighbors.line9.comment
# 017096.python.hook-sklearn.neighbors.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017097.python.hook-sklearn.neighbors.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies

hiddenimports = []

if is_module_satisfies("scikit_learn > 1.0.1"):
    # 017098.python.hook-sklearn.neighbors.line18.comment 1.0.2 and later
    hiddenimports += [
        'sklearn.neighbors._quad_tree',
    ]
elif is_module_satisfies("scikit_learn < 0.22 "):
    # 017099.python.hook-sklearn.neighbors.line23.comment 0.21 and below
    hiddenimports += [
        'sklearn.neighbors.typedefs',
        'sklearn.neighbors.quad_tree',
    ]
else:
    # 017100.python.hook-sklearn.neighbors.line29.comment between and including 0.22 and 1.0.1
    hiddenimports += [
        'sklearn.neighbors._typedefs',
        'sklearn.neighbors._quad_tree',
    ]

# 017101.python.hook-sklearn.neighbors.line35.comment The following hidden import must be added here
# 017102.python.hook-sklearn.neighbors.line36.comment (as opposed to sklearn.tree)
hiddenimports += ['sklearn.tree._criterion']

# 017103.python.hook-sklearn.neighbors.line39.comment Additional hidden imports introduced in v1.0.0
if is_module_satisfies("scikit_learn >= 1.0.0"):
    hiddenimports += ["sklearn.neighbors._partition_nodes"]
