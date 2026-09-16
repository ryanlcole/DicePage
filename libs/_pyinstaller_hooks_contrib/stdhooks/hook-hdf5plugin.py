# 013869.python.hook-hdf5plugin.line1.comment ------------------------------------------------------------------
# 013870.python.hook-hdf5plugin.line2.comment Copyright (c) 2022 PyInstaller Development Team.
# 013871.python.hook-hdf5plugin.line3.comment
# 013872.python.hook-hdf5plugin.line4.comment This file is distributed under the terms of the GNU General Public
# 013873.python.hook-hdf5plugin.line5.comment License (version 2.0 or later).
# 013874.python.hook-hdf5plugin.line6.comment
# 013875.python.hook-hdf5plugin.line7.comment The full license is available in LICENSE, distributed with
# 013876.python.hook-hdf5plugin.line8.comment this software.
# 013877.python.hook-hdf5plugin.line9.comment
# 013878.python.hook-hdf5plugin.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013879.python.hook-hdf5plugin.line11.comment ------------------------------------------------------------------

# 013880.python.hook-hdf5plugin.line13.comment Hook for hdf5plugin: https://pypi.org/project/hdf5plugin/

from PyInstaller.utils.hooks import collect_dynamic_libs

datas = collect_dynamic_libs("hdf5plugin")
