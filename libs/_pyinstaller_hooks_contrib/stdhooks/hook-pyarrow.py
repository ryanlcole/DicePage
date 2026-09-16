# 015499.python.hook-pyarrow.line1.comment ------------------------------------------------------------------
# 015500.python.hook-pyarrow.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 015501.python.hook-pyarrow.line3.comment
# 015502.python.hook-pyarrow.line4.comment This file is distributed under the terms of the GNU General Public
# 015503.python.hook-pyarrow.line5.comment License (version 2.0 or later).
# 015504.python.hook-pyarrow.line6.comment
# 015505.python.hook-pyarrow.line7.comment The full license is available in LICENSE, distributed with
# 015506.python.hook-pyarrow.line8.comment this software.
# 015507.python.hook-pyarrow.line9.comment
# 015508.python.hook-pyarrow.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015509.python.hook-pyarrow.line11.comment ------------------------------------------------------------------

# 015510.python.hook-pyarrow.line13.comment Hook for https://pypi.org/project/pyarrow/

from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs

hiddenimports = collect_submodules('pyarrow', filter=lambda x: "tests" not in x)
datas = collect_data_files('pyarrow')
binaries = collect_dynamic_libs('pyarrow')
