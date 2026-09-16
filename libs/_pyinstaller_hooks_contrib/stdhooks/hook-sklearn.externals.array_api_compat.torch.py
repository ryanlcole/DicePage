# 017018.python.hook-sklearn.externals.array_api_compat.torch.line1.comment ------------------------------------------------------------------
# 017019.python.hook-sklearn.externals.array_api_compat.torch.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 017020.python.hook-sklearn.externals.array_api_compat.torch.line3.comment
# 017021.python.hook-sklearn.externals.array_api_compat.torch.line4.comment This file is distributed under the terms of the GNU General Public
# 017022.python.hook-sklearn.externals.array_api_compat.torch.line5.comment License (version 2.0 or later).
# 017023.python.hook-sklearn.externals.array_api_compat.torch.line6.comment
# 017024.python.hook-sklearn.externals.array_api_compat.torch.line7.comment The full license is available in LICENSE, distributed with
# 017025.python.hook-sklearn.externals.array_api_compat.torch.line8.comment this software.
# 017026.python.hook-sklearn.externals.array_api_compat.torch.line9.comment
# 017027.python.hook-sklearn.externals.array_api_compat.torch.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017028.python.hook-sklearn.externals.array_api_compat.torch.line11.comment ------------------------------------------------------------------

# 017029.python.hook-sklearn.externals.array_api_compat.torch.line13.comment These hidden imports are required due to the following statements found in the package's `__init__.py`:
# 017030.python.hook-sklearn.externals.array_api_compat.torch.line14.comment ```
# 017031.python.hook-sklearn.externals.array_api_compat.torch.line15.comment __import__(__package__ + '.linalg')
# 017032.python.hook-sklearn.externals.array_api_compat.torch.line16.comment __import__(__package__ + '.fft')
# 017033.python.hook-sklearn.externals.array_api_compat.torch.line17.comment ```
hiddenimports = [
    'sklearn.externals.array_api_compat.torch.fft',
    'sklearn.externals.array_api_compat.torch.linalg',
]
