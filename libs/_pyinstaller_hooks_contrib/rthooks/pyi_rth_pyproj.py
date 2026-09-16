# 011588.python.pyi_rth_pyproj.line1.comment -----------------------------------------------------------------------------
# 011589.python.pyi_rth_pyproj.line2.comment Copyright (c) 2015-2020, PyInstaller Development Team.
# 011590.python.pyi_rth_pyproj.line3.comment
# 011591.python.pyi_rth_pyproj.line4.comment This file is distributed under the terms of the Apache License 2.0
# 011592.python.pyi_rth_pyproj.line5.comment
# 011593.python.pyi_rth_pyproj.line6.comment The full license is available in LICENSE, distributed with
# 011594.python.pyi_rth_pyproj.line7.comment this software.
# 011595.python.pyi_rth_pyproj.line8.comment
# 011596.python.pyi_rth_pyproj.line9.comment SPDX-License-Identifier: Apache-2.0
# 011597.python.pyi_rth_pyproj.line10.comment -----------------------------------------------------------------------------

import os
import sys

# 011598.python.pyi_rth_pyproj.line15.comment Installing `pyproj` Conda packages requires to set `PROJ_LIB`

is_win = sys.platform.startswith('win')
if is_win:

    proj_data = os.path.join(sys._MEIPASS, 'Library', 'share', 'proj')

else:
    proj_data = os.path.join(sys._MEIPASS, 'share', 'proj')

if os.path.exists(proj_data):
    os.environ['PROJ_LIB'] = proj_data
