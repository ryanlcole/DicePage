# 016986.python.hook-sklearn.externals.array_api_compat.dask.array.line1.comment ------------------------------------------------------------------
# 016987.python.hook-sklearn.externals.array_api_compat.dask.array.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 016988.python.hook-sklearn.externals.array_api_compat.dask.array.line3.comment
# 016989.python.hook-sklearn.externals.array_api_compat.dask.array.line4.comment This file is distributed under the terms of the GNU General Public
# 016990.python.hook-sklearn.externals.array_api_compat.dask.array.line5.comment License (version 2.0 or later).
# 016991.python.hook-sklearn.externals.array_api_compat.dask.array.line6.comment
# 016992.python.hook-sklearn.externals.array_api_compat.dask.array.line7.comment The full license is available in LICENSE, distributed with
# 016993.python.hook-sklearn.externals.array_api_compat.dask.array.line8.comment this software.
# 016994.python.hook-sklearn.externals.array_api_compat.dask.array.line9.comment
# 016995.python.hook-sklearn.externals.array_api_compat.dask.array.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016996.python.hook-sklearn.externals.array_api_compat.dask.array.line11.comment ------------------------------------------------------------------

# 016997.python.hook-sklearn.externals.array_api_compat.dask.array.line13.comment These hidden imports are required due to the following statements found in the package's `__init__.py`:
# 016998.python.hook-sklearn.externals.array_api_compat.dask.array.line14.comment ```
# 016999.python.hook-sklearn.externals.array_api_compat.dask.array.line15.comment __import__(__package__ + '.linalg')
# 017000.python.hook-sklearn.externals.array_api_compat.dask.array.line16.comment __import__(__package__ + '.fft')
# 017001.python.hook-sklearn.externals.array_api_compat.dask.array.line17.comment ```
hiddenimports = [
    'sklearn.externals.array_api_compat.dask.array.fft',
    'sklearn.externals.array_api_compat.dask.array.linalg',
]
