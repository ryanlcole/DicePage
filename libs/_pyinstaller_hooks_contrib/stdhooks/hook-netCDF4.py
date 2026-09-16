# 014800.python.hook-netCDF4.line1.comment ------------------------------------------------------------------
# 014801.python.hook-netCDF4.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014802.python.hook-netCDF4.line3.comment
# 014803.python.hook-netCDF4.line4.comment This file is distributed under the terms of the GNU General Public
# 014804.python.hook-netCDF4.line5.comment License (version 2.0 or later).
# 014805.python.hook-netCDF4.line6.comment
# 014806.python.hook-netCDF4.line7.comment The full license is available in LICENSE, distributed with
# 014807.python.hook-netCDF4.line8.comment this software.
# 014808.python.hook-netCDF4.line9.comment
# 014809.python.hook-netCDF4.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014810.python.hook-netCDF4.line11.comment ------------------------------------------------------------------

from PyInstaller.compat import is_win
from PyInstaller.utils.hooks import is_module_satisfies

# 014811.python.hook-netCDF4.line16.comment netCDF4 (tested with v.1.1.9) has some hidden imports
hiddenimports = ['netCDF4.utils']

# 014812.python.hook-netCDF4.line19.comment Around netCDF4 1.4.0, netcdftime changed name to cftime
if is_module_satisfies("netCDF4 < 1.4.0"):
    hiddenimports += ['netcdftime']
else:
    hiddenimports += ['cftime']

# 014813.python.hook-netCDF4.line25.comment Starting with netCDF 1.6.4, certifi is a hidden import made in
# 014814.python.hook-netCDF4.line26.comment netCDF4/_netCDF4.pyx.
if is_module_satisfies("netCDF4 >= 1.6.4"):
    hiddenimports += ['certifi']

# 014815.python.hook-netCDF4.line30.comment netCDF 1.6.2 is the first version that uses `delvewheel` for bundling DLLs in Windows PyPI wheels. While contemporary
# 014816.python.hook-netCDF4.line31.comment PyInstaller versions automatically pick up DLLs from external `netCDF4.libs` directory, this does not work on Anaconda
# 014817.python.hook-netCDF4.line32.comment python 3.8 and 3.9 due to defunct `os.add_dll_directory`, which forces `delvewheel` to use the old load-order file
# 014818.python.hook-netCDF4.line33.comment approach. So we need to explicitly ensure that load-order file as well as DLLs are collected.
if is_win and is_module_satisfies("netCDF4 >= 1.6.2"):
    if is_module_satisfies("PyInstaller >= 5.6"):
        from PyInstaller.utils.hooks import collect_delvewheel_libs_directory
        datas, binaries = collect_delvewheel_libs_directory("netCDF4")
