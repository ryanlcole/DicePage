# 012263.python.hook-bleak.line1.comment ------------------------------------------------------------------
# 012264.python.hook-bleak.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012265.python.hook-bleak.line3.comment
# 012266.python.hook-bleak.line4.comment This file is distributed under the terms of the GNU General Public
# 012267.python.hook-bleak.line5.comment License (version 2.0 or later).
# 012268.python.hook-bleak.line6.comment
# 012269.python.hook-bleak.line7.comment The full license is available in LICENSE, distributed with
# 012270.python.hook-bleak.line8.comment this software.
# 012271.python.hook-bleak.line9.comment
# 012272.python.hook-bleak.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012273.python.hook-bleak.line11.comment ------------------------------------------------------------------
# 012274.python.hook-bleak.line12.comment hook for https://github.com/hbldh/bleak

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs
from PyInstaller.compat import is_win

if is_win:
    datas = collect_data_files('bleak', subdir=r'backends\dotnet')
    binaries = collect_dynamic_libs('bleak')
