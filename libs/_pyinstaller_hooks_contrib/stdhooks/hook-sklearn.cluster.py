# 016957.python.hook-sklearn.cluster.line1.comment ------------------------------------------------------------------
# 016958.python.hook-sklearn.cluster.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016959.python.hook-sklearn.cluster.line3.comment
# 016960.python.hook-sklearn.cluster.line4.comment This file is distributed under the terms of the GNU General Public
# 016961.python.hook-sklearn.cluster.line5.comment License (version 2.0 or later).
# 016962.python.hook-sklearn.cluster.line6.comment
# 016963.python.hook-sklearn.cluster.line7.comment The full license is available in LICENSE, distributed with
# 016964.python.hook-sklearn.cluster.line8.comment this software.
# 016965.python.hook-sklearn.cluster.line9.comment
# 016966.python.hook-sklearn.cluster.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016967.python.hook-sklearn.cluster.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies

# 016968.python.hook-sklearn.cluster.line15.comment sklearn.cluster in scikit-learn 0.23.x has a hidden import of
# 016969.python.hook-sklearn.cluster.line16.comment threadpoolctl
if is_module_satisfies("scikit_learn >= 0.23"):
    hiddenimports = ['threadpoolctl', ]
