# 016227.python.hook-pysnmp.line1.comment ------------------------------------------------------------------
# 016228.python.hook-pysnmp.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016229.python.hook-pysnmp.line3.comment
# 016230.python.hook-pysnmp.line4.comment This file is distributed under the terms of the GNU General Public
# 016231.python.hook-pysnmp.line5.comment License (version 2.0 or later).
# 016232.python.hook-pysnmp.line6.comment
# 016233.python.hook-pysnmp.line7.comment The full license is available in LICENSE, distributed with
# 016234.python.hook-pysnmp.line8.comment this software.
# 016235.python.hook-pysnmp.line9.comment
# 016236.python.hook-pysnmp.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016237.python.hook-pysnmp.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = collect_submodules('pysnmp.smi.mibs')
datas = collect_data_files('pysnmp.smi.mibs', include_py_files=True)
