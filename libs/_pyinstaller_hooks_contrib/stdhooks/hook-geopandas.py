# 013563.python.hook-geopandas.line1.comment ------------------------------------------------------------------
# 013564.python.hook-geopandas.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 013565.python.hook-geopandas.line3.comment
# 013566.python.hook-geopandas.line4.comment This file is distributed under the terms of the GNU General Public
# 013567.python.hook-geopandas.line5.comment License (version 2.0 or later).
# 013568.python.hook-geopandas.line6.comment
# 013569.python.hook-geopandas.line7.comment The full license is available in LICENSE, distributed with
# 013570.python.hook-geopandas.line8.comment this software.
# 013571.python.hook-geopandas.line9.comment
# 013572.python.hook-geopandas.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013573.python.hook-geopandas.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("geopandas", subdir="datasets")
