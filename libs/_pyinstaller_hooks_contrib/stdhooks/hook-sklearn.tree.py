# 017116.python.hook-sklearn.tree.line1.comment ------------------------------------------------------------------
# 017117.python.hook-sklearn.tree.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 017118.python.hook-sklearn.tree.line3.comment
# 017119.python.hook-sklearn.tree.line4.comment This file is distributed under the terms of the GNU General Public
# 017120.python.hook-sklearn.tree.line5.comment License (version 2.0 or later).
# 017121.python.hook-sklearn.tree.line6.comment
# 017122.python.hook-sklearn.tree.line7.comment The full license is available in LICENSE, distributed with
# 017123.python.hook-sklearn.tree.line8.comment this software.
# 017124.python.hook-sklearn.tree.line9.comment
# 017125.python.hook-sklearn.tree.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017126.python.hook-sklearn.tree.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies

hiddenimports = ['sklearn.tree._utils']

if is_module_satisfies('scikit-learn >= 1.6.0'):
    hiddenimports += ['sklearn.tree._partitioner']
