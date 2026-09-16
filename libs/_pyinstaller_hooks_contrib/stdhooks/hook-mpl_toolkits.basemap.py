# 014662.python.hook-mpl_toolkits.basemap.line1.comment ------------------------------------------------------------------
# 014663.python.hook-mpl_toolkits.basemap.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014664.python.hook-mpl_toolkits.basemap.line3.comment
# 014665.python.hook-mpl_toolkits.basemap.line4.comment This file is distributed under the terms of the GNU General Public
# 014666.python.hook-mpl_toolkits.basemap.line5.comment License (version 2.0 or later).
# 014667.python.hook-mpl_toolkits.basemap.line6.comment
# 014668.python.hook-mpl_toolkits.basemap.line7.comment The full license is available in LICENSE, distributed with
# 014669.python.hook-mpl_toolkits.basemap.line8.comment this software.
# 014670.python.hook-mpl_toolkits.basemap.line9.comment
# 014671.python.hook-mpl_toolkits.basemap.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014672.python.hook-mpl_toolkits.basemap.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.compat import is_win, base_prefix

import os

# 014673.python.hook-mpl_toolkits.basemap.line18.comment mpl_toolkits.basemap (tested with v.1.0.7) is shipped with auxiliary data,
# 014674.python.hook-mpl_toolkits.basemap.line19.comment usually stored in mpl_toolkits\basemap\data and used to plot maps
datas = collect_data_files('mpl_toolkits.basemap', subdir='data')

# 014675.python.hook-mpl_toolkits.basemap.line22.comment check if the data has been effectively found
if len(datas) == 0:

    # 014676.python.hook-mpl_toolkits.basemap.line25.comment - conda-specific

    if is_win:
        tgt_basemap_data = os.path.join('Library', 'share', 'basemap')
        src_basemap_data = os.path.join(base_prefix, 'Library', 'share', 'basemap')

    else:  # both linux and darwin
        tgt_basemap_data = os.path.join('share', 'basemap')
        src_basemap_data = os.path.join(base_prefix, 'share', 'basemap')

    if os.path.exists(src_basemap_data):
        datas.append((src_basemap_data, tgt_basemap_data))
