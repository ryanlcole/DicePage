# 017127.python.hook-sklearn.utils.line1.comment ------------------------------------------------------------------
# 017128.python.hook-sklearn.utils.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 017129.python.hook-sklearn.utils.line3.comment
# 017130.python.hook-sklearn.utils.line4.comment This file is distributed under the terms of the GNU General Public
# 017131.python.hook-sklearn.utils.line5.comment License (version 2.0 or later).
# 017132.python.hook-sklearn.utils.line6.comment
# 017133.python.hook-sklearn.utils.line7.comment The full license is available in LICENSE, distributed with
# 017134.python.hook-sklearn.utils.line8.comment this software.
# 017135.python.hook-sklearn.utils.line9.comment
# 017136.python.hook-sklearn.utils.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017137.python.hook-sklearn.utils.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies

hiddenimports = ['sklearn.utils._cython_blas']

# 017138.python.hook-sklearn.utils.line17.comment As of scikit-learn 1.7.1, the `sklearn.utils._isfinite` extension started to depend on newly-introduced
# 017139.python.hook-sklearn.utils.line18.comment `sklearn._cyutility`.
if is_module_satisfies('scikit-learn >= 1.7.1'):
    hiddenimports += ['sklearn._cyutility']
