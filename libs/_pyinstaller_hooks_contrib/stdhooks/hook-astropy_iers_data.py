# 012113.python.hook-astropy_iers_data.line1.comment ------------------------------------------------------------------
# 012114.python.hook-astropy_iers_data.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012115.python.hook-astropy_iers_data.line3.comment
# 012116.python.hook-astropy_iers_data.line4.comment This file is distributed under the terms of the GNU General Public
# 012117.python.hook-astropy_iers_data.line5.comment License (version 2.0 or later).
# 012118.python.hook-astropy_iers_data.line6.comment
# 012119.python.hook-astropy_iers_data.line7.comment The full license is available in LICENSE, distributed with
# 012120.python.hook-astropy_iers_data.line8.comment this software.
# 012121.python.hook-astropy_iers_data.line9.comment
# 012122.python.hook-astropy_iers_data.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012123.python.hook-astropy_iers_data.line11.comment ------------------------------------------------------------------

# 012124.python.hook-astropy_iers_data.line13.comment Hook for https://github.com/astropy/astropy-iers-data

from PyInstaller.utils.hooks import collect_data_files
datas = collect_data_files("astropy_iers_data")
