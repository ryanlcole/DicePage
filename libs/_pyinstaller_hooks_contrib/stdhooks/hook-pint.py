# 015331.python.hook-pint.line1.comment ------------------------------------------------------------------
# 015332.python.hook-pint.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 015333.python.hook-pint.line3.comment
# 015334.python.hook-pint.line4.comment This file is distributed under the terms of the GNU General Public
# 015335.python.hook-pint.line5.comment License (version 2.0 or later).
# 015336.python.hook-pint.line6.comment
# 015337.python.hook-pint.line7.comment The full license is available in LICENSE, distributed with
# 015338.python.hook-pint.line8.comment this software.
# 015339.python.hook-pint.line9.comment
# 015340.python.hook-pint.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015341.python.hook-pint.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, copy_metadata

datas = collect_data_files('pint')
datas += copy_metadata('pint')
