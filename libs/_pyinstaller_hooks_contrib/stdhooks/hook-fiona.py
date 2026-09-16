# 013397.python.hook-fiona.line1.comment ------------------------------------------------------------------
# 013398.python.hook-fiona.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 013399.python.hook-fiona.line3.comment
# 013400.python.hook-fiona.line4.comment This file is distributed under the terms of the GNU General Public
# 013401.python.hook-fiona.line5.comment License (version 2.0 or later).
# 013402.python.hook-fiona.line6.comment
# 013403.python.hook-fiona.line7.comment The full license is available in LICENSE, distributed with
# 013404.python.hook-fiona.line8.comment this software.
# 013405.python.hook-fiona.line9.comment
# 013406.python.hook-fiona.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013407.python.hook-fiona.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, is_module_satisfies

hiddenimports = [
    "fiona._shim",
    "fiona.schema",
    "json",
]

# 013408.python.hook-fiona.line21.comment As of fiona 1.9.0, `fiona.enums` is also a hidden import, made in cythonized `fiona.crs`.
if is_module_satisfies("fiona >= 1.9.0"):
    hiddenimports.append("fiona.enums")

# 013409.python.hook-fiona.line25.comment Collect data files that are part of the package (e.g., projections database)
datas = collect_data_files("fiona")
