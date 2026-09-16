# 014908.python.hook-numcodecs.line1.comment ------------------------------------------------------------------
# 014909.python.hook-numcodecs.line2.comment Copyright (c) 2022 PyInstaller Development Team.
# 014910.python.hook-numcodecs.line3.comment
# 014911.python.hook-numcodecs.line4.comment This file is distributed under the terms of the GNU General Public
# 014912.python.hook-numcodecs.line5.comment License (version 2.0 or later).
# 014913.python.hook-numcodecs.line6.comment
# 014914.python.hook-numcodecs.line7.comment The full license is available in LICENSE, distributed with
# 014915.python.hook-numcodecs.line8.comment this software.
# 014916.python.hook-numcodecs.line9.comment
# 014917.python.hook-numcodecs.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014918.python.hook-numcodecs.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies

# 014919.python.hook-numcodecs.line15.comment compat_ext is only imported from pyx files, so it is missed
hiddenimports = ['numcodecs.compat_ext']

# 014920.python.hook-numcodecs.line18.comment numcodecs v0.15.0 added an import of `deprecated` (from `Deprecated` dist) in one of its cythonized extension.
if is_module_satisfies('numcodecs >= 0.15.0'):
    hiddenimports += ['deprecated']
