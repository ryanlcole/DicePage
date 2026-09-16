# 015144.python.hook-osgeo.line1.comment ------------------------------------------------------------------
# 015145.python.hook-osgeo.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 015146.python.hook-osgeo.line3.comment
# 015147.python.hook-osgeo.line4.comment This file is distributed under the terms of the GNU General Public
# 015148.python.hook-osgeo.line5.comment License (version 2.0 or later).
# 015149.python.hook-osgeo.line6.comment
# 015150.python.hook-osgeo.line7.comment The full license is available in LICENSE, distributed with
# 015151.python.hook-osgeo.line8.comment this software.
# 015152.python.hook-osgeo.line9.comment
# 015153.python.hook-osgeo.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015154.python.hook-osgeo.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.compat import is_win, is_darwin

import os
import sys

# 015155.python.hook-osgeo.line19.comment The osgeo libraries require auxiliary data and may have hidden dependencies.
# 015156.python.hook-osgeo.line20.comment There are several possible configurations on how these libraries can be
# 015157.python.hook-osgeo.line21.comment deployed.
# 015158.python.hook-osgeo.line22.comment This hook evaluates the cases when:
# 015159.python.hook-osgeo.line23.comment - the `data` folder is present "in-source" (sharing the same namespace folder
# 015160.python.hook-osgeo.line24.comment as the code libraries)
# 015161.python.hook-osgeo.line25.comment - the `data` folder is present "out-source" (for instance, on Anaconda for
# 015162.python.hook-osgeo.line26.comment Windows, in PYTHONHOME/Library/data)
# 015163.python.hook-osgeo.line27.comment In this latter case, the hook also checks for the presence of `proj` library
# 015164.python.hook-osgeo.line28.comment (e.g., on Windows in PYTHONHOME) for being added to the bundle.
# 015165.python.hook-osgeo.line29.comment
# 015166.python.hook-osgeo.line30.comment This hook has been tested with gdal (v.1.11.2 and 1.11.3) on:
# 015167.python.hook-osgeo.line31.comment - Win 7 and 10 64bit
# 015168.python.hook-osgeo.line32.comment - Ubuntu 15.04 64bit
# 015169.python.hook-osgeo.line33.comment - Mac OS X Yosemite 10.10
# 015170.python.hook-osgeo.line34.comment
# 015171.python.hook-osgeo.line35.comment TODO: Fix for gdal>=2.0.0, <2.0.3: 'NameError: global name 'help' is not defined'

# 015172.python.hook-osgeo.line37.comment flag used to identify an Anaconda environment
is_conda = False

# 015173.python.hook-osgeo.line40.comment Auxiliary data:
# 015174.python.hook-osgeo.line41.comment
# 015175.python.hook-osgeo.line42.comment - general case (data in 'osgeo/data'):
datas = collect_data_files('osgeo', subdir='data')

# 015176.python.hook-osgeo.line45.comment check if the data has been effectively found in 'osgeo/data/gdal'
if len(datas) == 0:

    if hasattr(sys, 'real_prefix'):  # check if in a virtual environment
        root_path = sys.real_prefix
    else:
        root_path = sys.prefix

    # 015178.python.hook-osgeo.line53.comment - conda-specific
    if is_win:
        tgt_gdal_data = os.path.join('Library', 'share', 'gdal')
        src_gdal_data = os.path.join(root_path, 'Library', 'share', 'gdal')
        if not os.path.exists(src_gdal_data):
            tgt_gdal_data = os.path.join('Library', 'data')
            src_gdal_data = os.path.join(root_path, 'Library', 'data')

    else:  # both linux and darwin
        tgt_gdal_data = os.path.join('share', 'gdal')
        src_gdal_data = os.path.join(root_path, 'share', 'gdal')

    if os.path.exists(src_gdal_data):
        is_conda = True
        datas.append((src_gdal_data, tgt_gdal_data))
        # 015180.python.hook-osgeo.line68.comment a real-time hook takes case to define the path for `GDAL_DATA`

# 015181.python.hook-osgeo.line70.comment Hidden dependencies
if is_conda:
    # 015182.python.hook-osgeo.line72.comment if `proj.4` is present, it provides additional functionalities
    if is_win:
        proj4_lib = os.path.join(root_path, 'proj.dll')
    elif is_darwin:
        proj4_lib = os.path.join(root_path, 'lib', 'libproj.dylib')
    else:  # assumed linux-like settings
        proj4_lib = os.path.join(root_path, 'lib', 'libproj.so')

    if os.path.exists(proj4_lib):
        binaries = [(proj4_lib, ".")]
