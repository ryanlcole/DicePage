# 016111.python.hook-pyproj.line1.comment ------------------------------------------------------------------
# 016112.python.hook-pyproj.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016113.python.hook-pyproj.line3.comment
# 016114.python.hook-pyproj.line4.comment This file is distributed under the terms of the GNU General Public
# 016115.python.hook-pyproj.line5.comment License (version 2.0 or later).
# 016116.python.hook-pyproj.line6.comment
# 016117.python.hook-pyproj.line7.comment The full license is available in LICENSE, distributed with
# 016118.python.hook-pyproj.line8.comment this software.
# 016119.python.hook-pyproj.line9.comment
# 016120.python.hook-pyproj.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016121.python.hook-pyproj.line11.comment ------------------------------------------------------------------

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, is_module_satisfies, copy_metadata
from PyInstaller.compat import is_win

hiddenimports = [
    "pyproj.datadir"
]

binaries = []

# 016122.python.hook-pyproj.line24.comment Versions prior to 2.3.0 also require pyproj._datadir
if not is_module_satisfies("pyproj >= 2.3.0"):
    hiddenimports += ["pyproj._datadir"]

# 016123.python.hook-pyproj.line28.comment Starting with version 3.0.0, pyproj._compat is needed
if is_module_satisfies("pyproj >= 3.0.0"):
    hiddenimports += ["pyproj._compat"]
    # 016124.python.hook-pyproj.line31.comment Linux and macOS also require distutils.
    if not is_win:
        hiddenimports += ["distutils.util"]

# 016125.python.hook-pyproj.line35.comment Data collection
datas = collect_data_files('pyproj')

# 016126.python.hook-pyproj.line38.comment Repackagers may de-vendor the proj data directory (Conda, Debian)
if not any(dest.startswith("pyproj/proj_dir") for (_, dest) in datas):
    if hasattr(sys, 'real_prefix'):  # check if in a virtual environment
        root_path = sys.real_prefix
    else:
        root_path = sys.prefix

    if is_win:
        tgt_proj_data = os.path.join('Library', 'share', 'proj')
        src_proj_data = os.path.join(root_path, 'Library', 'share', 'proj')

    else:  # both linux and darwin
        tgt_proj_data = os.path.join('share', 'proj')
        src_proj_data = os.path.join(root_path, 'share', 'proj')

    if os.path.exists(src_proj_data):
        datas.append((src_proj_data, tgt_proj_data))
        # 016129.python.hook-pyproj.line55.comment A runtime hook defines the path for `PROJ_LIB`
    else:
        from PyInstaller.utils.hooks import logger
        logger.warning("Datas for pyproj not found at:\n{}".format(src_proj_data))

# 016130.python.hook-pyproj.line60.comment With pyproj 3.4.0, we need to collect package's metadata due to `importlib.metadata.version(__package__)` call in
# 016131.python.hook-pyproj.line61.comment `__init__.py`. This change was reverted in subsequent releases of pyproj, so we collect metadata only for 3.4.0.
if is_module_satisfies("pyproj == 3.4.0"):
    datas += copy_metadata("pyproj")

# 016132.python.hook-pyproj.line65.comment pyproj 3.4.0 was also the first release that used `delvewheel` for its Windows PyPI wheels. While contemporary
# 016133.python.hook-pyproj.line66.comment PyInstaller versions automatically pick up DLLs from external `pyproj.libs` directory, this does not work on Anaconda
# 016134.python.hook-pyproj.line67.comment python 3.8 and 3.9 due to defunct `os.add_dll_directory`, which forces `delvewheel` to use the old load-order file
# 016135.python.hook-pyproj.line68.comment approach. So we need to explicitly ensure that load-order file as well as DLLs are collected.
if is_win and is_module_satisfies("pyproj >= 3.4.0"):
    if is_module_satisfies("PyInstaller >= 5.6"):
        from PyInstaller.utils.hooks import collect_delvewheel_libs_directory
        datas, binaries = collect_delvewheel_libs_directory("pyproj", datas=datas, binaries=binaries)
