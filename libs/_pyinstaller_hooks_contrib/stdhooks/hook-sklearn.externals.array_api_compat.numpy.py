# 017002.python.hook-sklearn.externals.array_api_compat.numpy.line1.comment ------------------------------------------------------------------
# 017003.python.hook-sklearn.externals.array_api_compat.numpy.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 017004.python.hook-sklearn.externals.array_api_compat.numpy.line3.comment
# 017005.python.hook-sklearn.externals.array_api_compat.numpy.line4.comment This file is distributed under the terms of the GNU General Public
# 017006.python.hook-sklearn.externals.array_api_compat.numpy.line5.comment License (version 2.0 or later).
# 017007.python.hook-sklearn.externals.array_api_compat.numpy.line6.comment
# 017008.python.hook-sklearn.externals.array_api_compat.numpy.line7.comment The full license is available in LICENSE, distributed with
# 017009.python.hook-sklearn.externals.array_api_compat.numpy.line8.comment this software.
# 017010.python.hook-sklearn.externals.array_api_compat.numpy.line9.comment
# 017011.python.hook-sklearn.externals.array_api_compat.numpy.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017012.python.hook-sklearn.externals.array_api_compat.numpy.line11.comment ------------------------------------------------------------------

# 017013.python.hook-sklearn.externals.array_api_compat.numpy.line13.comment These hidden imports are required due to the following statements found in the package's `__init__.py`:
# 017014.python.hook-sklearn.externals.array_api_compat.numpy.line14.comment ```
# 017015.python.hook-sklearn.externals.array_api_compat.numpy.line15.comment __import__(__package__ + '.linalg')
# 017016.python.hook-sklearn.externals.array_api_compat.numpy.line16.comment __import__(__package__ + '.fft')
# 017017.python.hook-sklearn.externals.array_api_compat.numpy.line17.comment ```
hiddenimports = [
    'sklearn.externals.array_api_compat.numpy.fft',
    'sklearn.externals.array_api_compat.numpy.linalg',
]
