# 018230.python.hook-uniseg.line1.comment ------------------------------------------------------------------
# 018231.python.hook-uniseg.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 018232.python.hook-uniseg.line3.comment
# 018233.python.hook-uniseg.line4.comment This file is distributed under the terms of the GNU General Public
# 018234.python.hook-uniseg.line5.comment License (version 2.0 or later).
# 018235.python.hook-uniseg.line6.comment
# 018236.python.hook-uniseg.line7.comment The full license is available in LICENSE, distributed with
# 018237.python.hook-uniseg.line8.comment this software.
# 018238.python.hook-uniseg.line9.comment
# 018239.python.hook-uniseg.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018240.python.hook-uniseg.line11.comment ------------------------------------------------------------------

# 018241.python.hook-uniseg.line13.comment Hook for the uniseg module: https://pypi.python.org/pypi/uniseg

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('uniseg')
