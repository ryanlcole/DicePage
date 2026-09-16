# 016149.python.hook-pypylon.line1.comment ------------------------------------------------------------------
# 016150.python.hook-pypylon.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016151.python.hook-pypylon.line3.comment
# 016152.python.hook-pypylon.line4.comment This file is distributed under the terms of the GNU General Public
# 016153.python.hook-pypylon.line5.comment License (version 2.0 or later).
# 016154.python.hook-pypylon.line6.comment
# 016155.python.hook-pypylon.line7.comment The full license is available in LICENSE, distributed with
# 016156.python.hook-pypylon.line8.comment this software.
# 016157.python.hook-pypylon.line9.comment
# 016158.python.hook-pypylon.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016159.python.hook-pypylon.line11.comment ------------------------------------------------------------------

# 016160.python.hook-pypylon.line13.comment PyPylon is a tricky library to bundle. It encapsulates the pylon C++ SDK inside
# 016161.python.hook-pypylon.line14.comment it with modified library references to make the module relocatable.
# 016162.python.hook-pypylon.line15.comment PyInstaller is able to find those libraries and preserve the linkage for almost
# 016163.python.hook-pypylon.line16.comment all of them. However - there is an additional linking step happening at runtime,
# 016164.python.hook-pypylon.line17.comment when the library is creating the transport layer for the camera. This linking
# 016165.python.hook-pypylon.line18.comment will fail with the library files modified by pyinstaller.
# 016166.python.hook-pypylon.line19.comment As the module is already relocatable, we circumvent this issue by bundling
# 016167.python.hook-pypylon.line20.comment pypylon as-is - for pyinstaller we treat the shared library files as just data.

import os

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    is_module_satisfies
)

# 016168.python.hook-pypylon.line30.comment Collect dynamic libs as data (to prevent pyinstaller from modifying them).
# 016169.python.hook-pypylon.line31.comment NOTE: under PyInstaller 6.x, these files end up re-classified as binaries anyway.
datas = collect_dynamic_libs('pypylon')

# 016170.python.hook-pypylon.line34.comment Collect data files, looking for pypylon/pylonCXP/bin/ProducerCXP.cti, but other files may also be needed
datas += collect_data_files('pypylon')

# 016171.python.hook-pypylon.line37.comment NOTE: the part below is incompatible with PyInstaller 6.x, because `collect_data_files(..., include_py_files=True)`
# 016172.python.hook-pypylon.line38.comment does not include binary extensions anymore. In addition, `pyinstaller/pyinstaller@ecc218c` in PyInstaller 6.2 fixed
# 016173.python.hook-pypylon.line39.comment the module exclusion for relative imports, so the modules listed below actually end up excluded. Presumably this
# 016174.python.hook-pypylon.line40.comment part was necessary with older PyInstaller versions, so we keep it around, but disable it for PyInstaller >= 6.0.
if is_module_satisfies('PyInstaller < 6.0'):
    # 016175.python.hook-pypylon.line42.comment Exclude the C++-extensions from automatic search, add them manually as data files
    # 016176.python.hook-pypylon.line43.comment their dependencies were already handled with collect_dynamic_libs
    excludedimports = ['pypylon._pylon', 'pypylon._genicam']
    for filename, module in collect_data_files('pypylon', include_py_files=True):
        if (os.path.basename(filename).startswith('_pylon.')
                or os.path.basename(filename).startswith('_genicam.')):
            datas += [(filename, module)]
