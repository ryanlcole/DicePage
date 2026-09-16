# 012494.python.hook-cf_units.line1.comment ------------------------------------------------------------------
# 012495.python.hook-cf_units.line2.comment Copyright (c) 2022 PyInstaller Development Team.
# 012496.python.hook-cf_units.line3.comment
# 012497.python.hook-cf_units.line4.comment This file is distributed under the terms of the GNU General Public
# 012498.python.hook-cf_units.line5.comment License (version 2.0 or later).
# 012499.python.hook-cf_units.line6.comment
# 012500.python.hook-cf_units.line7.comment The full license is available in LICENSE, distributed with
# 012501.python.hook-cf_units.line8.comment this software.
# 012502.python.hook-cf_units.line9.comment
# 012503.python.hook-cf_units.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012504.python.hook-cf_units.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

# 012505.python.hook-cf_units.line15.comment Include data files from cf_units/etc sub-directory.
datas = collect_data_files('cf_units', includes=['etc/**'])
