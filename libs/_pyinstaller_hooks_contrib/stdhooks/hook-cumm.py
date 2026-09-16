# 012685.python.hook-cumm.line1.comment ------------------------------------------------------------------
# 012686.python.hook-cumm.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 012687.python.hook-cumm.line3.comment
# 012688.python.hook-cumm.line4.comment This file is distributed under the terms of the GNU General Public
# 012689.python.hook-cumm.line5.comment License (version 2.0 or later).
# 012690.python.hook-cumm.line6.comment
# 012691.python.hook-cumm.line7.comment The full license is available in LICENSE, distributed with
# 012692.python.hook-cumm.line8.comment this software.
# 012693.python.hook-cumm.line9.comment
# 012694.python.hook-cumm.line10.comment SPDX-License-Identifier: GPL-2.0-or-later

from PyInstaller.utils.hooks import collect_data_files

# 012695.python.hook-cumm.line14.comment Collect files from cumm/include directory - at import, the package asserts the existence of this directory.
datas = collect_data_files('cumm')
