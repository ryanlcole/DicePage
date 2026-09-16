# 013060.python.hook-eccodeslib.line1.comment ------------------------------------------------------------------
# 013061.python.hook-eccodeslib.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 013062.python.hook-eccodeslib.line3.comment
# 013063.python.hook-eccodeslib.line4.comment This file is distributed under the terms of the GNU General Public
# 013064.python.hook-eccodeslib.line5.comment License (version 2.0 or later).
# 013065.python.hook-eccodeslib.line6.comment
# 013066.python.hook-eccodeslib.line7.comment The full license is available in LICENSE, distributed with
# 013067.python.hook-eccodeslib.line8.comment this software.
# 013068.python.hook-eccodeslib.line9.comment
# 013069.python.hook-eccodeslib.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013070.python.hook-eccodeslib.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_dynamic_libs

# 013071.python.hook-eccodeslib.line15.comment Collect bundled dynamic libraries.
binaries = collect_dynamic_libs('eccodeslib')

# 013072.python.hook-eccodeslib.line18.comment `eccodeslib` depends on `eckitlib` and `fckitlib`, and when libraries are being imported at run-time by
# 013073.python.hook-eccodeslib.line19.comment `findlibs.find()` user warnings are emitted if these packages cannot be imported.
hiddenimports = ['eckitlib', 'fckitlib']
