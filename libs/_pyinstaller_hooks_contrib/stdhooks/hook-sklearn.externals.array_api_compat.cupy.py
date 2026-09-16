# 016970.python.hook-sklearn.externals.array_api_compat.cupy.line1.comment ------------------------------------------------------------------
# 016971.python.hook-sklearn.externals.array_api_compat.cupy.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 016972.python.hook-sklearn.externals.array_api_compat.cupy.line3.comment
# 016973.python.hook-sklearn.externals.array_api_compat.cupy.line4.comment This file is distributed under the terms of the GNU General Public
# 016974.python.hook-sklearn.externals.array_api_compat.cupy.line5.comment License (version 2.0 or later).
# 016975.python.hook-sklearn.externals.array_api_compat.cupy.line6.comment
# 016976.python.hook-sklearn.externals.array_api_compat.cupy.line7.comment The full license is available in LICENSE, distributed with
# 016977.python.hook-sklearn.externals.array_api_compat.cupy.line8.comment this software.
# 016978.python.hook-sklearn.externals.array_api_compat.cupy.line9.comment
# 016979.python.hook-sklearn.externals.array_api_compat.cupy.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016980.python.hook-sklearn.externals.array_api_compat.cupy.line11.comment ------------------------------------------------------------------

# 016981.python.hook-sklearn.externals.array_api_compat.cupy.line13.comment These hidden imports are required due to the following statements found in the package's `__init__.py`:
# 016982.python.hook-sklearn.externals.array_api_compat.cupy.line14.comment ```
# 016983.python.hook-sklearn.externals.array_api_compat.cupy.line15.comment __import__(__package__ + '.linalg')
# 016984.python.hook-sklearn.externals.array_api_compat.cupy.line16.comment __import__(__package__ + '.fft')
# 016985.python.hook-sklearn.externals.array_api_compat.cupy.line17.comment ```
hiddenimports = [
    'sklearn.externals.array_api_compat.cupy.fft',
    'sklearn.externals.array_api_compat.cupy.linalg',
]
