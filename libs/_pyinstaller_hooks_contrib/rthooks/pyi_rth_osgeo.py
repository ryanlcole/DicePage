# 011565.python.pyi_rth_osgeo.line1.comment -----------------------------------------------------------------------------
# 011566.python.pyi_rth_osgeo.line2.comment Copyright (c) 2015-2020, PyInstaller Development Team.
# 011567.python.pyi_rth_osgeo.line3.comment
# 011568.python.pyi_rth_osgeo.line4.comment This file is distributed under the terms of the Apache License 2.0
# 011569.python.pyi_rth_osgeo.line5.comment
# 011570.python.pyi_rth_osgeo.line6.comment The full license is available in LICENSE, distributed with
# 011571.python.pyi_rth_osgeo.line7.comment this software.
# 011572.python.pyi_rth_osgeo.line8.comment
# 011573.python.pyi_rth_osgeo.line9.comment SPDX-License-Identifier: Apache-2.0
# 011574.python.pyi_rth_osgeo.line10.comment -----------------------------------------------------------------------------

import os
import sys

# 011575.python.pyi_rth_osgeo.line15.comment Installing `osgeo` Conda packages requires to set `GDAL_DATA`

is_win = sys.platform.startswith('win')
if is_win:

    gdal_data = os.path.join(sys._MEIPASS, 'data', 'gdal')
    if not os.path.exists(gdal_data):

        gdal_data = os.path.join(sys._MEIPASS, 'Library', 'share', 'gdal')
        # 011576.python.pyi_rth_osgeo.line24.comment last attempt, check if one of the required file is in the generic folder Library/data
        if not os.path.exists(os.path.join(gdal_data, 'gcs.csv')):
            gdal_data = os.path.join(sys._MEIPASS, 'Library', 'data')

else:
    gdal_data = os.path.join(sys._MEIPASS, 'share', 'gdal')

if os.path.exists(gdal_data):
    os.environ['GDAL_DATA'] = gdal_data
