# 012506.python.hook-cftime.line1.comment ------------------------------------------------------------------
# 012507.python.hook-cftime.line2.comment Copyright (c) 2022 PyInstaller Development Team.
# 012508.python.hook-cftime.line3.comment
# 012509.python.hook-cftime.line4.comment This file is distributed under the terms of the GNU General Public
# 012510.python.hook-cftime.line5.comment License (version 2.0 or later).
# 012511.python.hook-cftime.line6.comment
# 012512.python.hook-cftime.line7.comment The full license is available in LICENSE, distributed with
# 012513.python.hook-cftime.line8.comment this software.
# 012514.python.hook-cftime.line9.comment
# 012515.python.hook-cftime.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012516.python.hook-cftime.line11.comment ------------------------------------------------------------------

# 012517.python.hook-cftime.line13.comment The cftime._cftime is a cython exension with following hidden imports:
hiddenimports = [
    're',
    'time',
    'datetime',
    'warnings',
    'numpy',
    'cftime._strptime',
]
