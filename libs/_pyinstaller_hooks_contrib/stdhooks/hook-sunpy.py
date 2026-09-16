# 017325.python.hook-sunpy.line1.comment ------------------------------------------------------------------
# 017326.python.hook-sunpy.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 017327.python.hook-sunpy.line3.comment
# 017328.python.hook-sunpy.line4.comment This file is distributed under the terms of the GNU General Public
# 017329.python.hook-sunpy.line5.comment License (version 2.0 or later).
# 017330.python.hook-sunpy.line6.comment
# 017331.python.hook-sunpy.line7.comment The full license is available in LICENSE, distributed with
# 017332.python.hook-sunpy.line8.comment this software.
# 017333.python.hook-sunpy.line9.comment
# 017334.python.hook-sunpy.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017335.python.hook-sunpy.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

hiddenimports = collect_submodules("sunpy", filter=lambda x: "tests" not in x.split("."))
datas = collect_data_files("sunpy", excludes=['**/tests/', '**/test/'])
datas += collect_data_files("drms")
datas += copy_metadata("sunpy")

# 017336.python.hook-sunpy.line20.comment Note : sunpy > 3.1.0 comes with it's own hook for running tests.
