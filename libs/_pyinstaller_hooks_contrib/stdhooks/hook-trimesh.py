# 018094.python.hook-trimesh.line1.comment ------------------------------------------------------------------
# 018095.python.hook-trimesh.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 018096.python.hook-trimesh.line3.comment
# 018097.python.hook-trimesh.line4.comment This file is distributed under the terms of the GNU General Public
# 018098.python.hook-trimesh.line5.comment License (version 2.0 or later).
# 018099.python.hook-trimesh.line6.comment
# 018100.python.hook-trimesh.line7.comment The full license is available in LICENSE, distributed with
# 018101.python.hook-trimesh.line8.comment this software.
# 018102.python.hook-trimesh.line9.comment
# 018103.python.hook-trimesh.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018104.python.hook-trimesh.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

# 018105.python.hook-trimesh.line15.comment Collect the *.json resource file.
# 018106.python.hook-trimesh.line16.comment This issue is reported in here: https://github.com/mikedh/trimesh/issues/412
datas = collect_data_files('trimesh')
