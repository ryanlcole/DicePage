# 013503.python.hook-fsspec.line1.comment ------------------------------------------------------------------
# 013504.python.hook-fsspec.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 013505.python.hook-fsspec.line3.comment
# 013506.python.hook-fsspec.line4.comment This file is distributed under the terms of the GNU General Public
# 013507.python.hook-fsspec.line5.comment License (version 2.0 or later).
# 013508.python.hook-fsspec.line6.comment
# 013509.python.hook-fsspec.line7.comment The full license is available in LICENSE, distributed with
# 013510.python.hook-fsspec.line8.comment this software.
# 013511.python.hook-fsspec.line9.comment
# 013512.python.hook-fsspec.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013513.python.hook-fsspec.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('fsspec')
