# 013354.python.hook-fastparquet.line1.comment ------------------------------------------------------------------
# 013355.python.hook-fastparquet.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 013356.python.hook-fastparquet.line3.comment
# 013357.python.hook-fastparquet.line4.comment This file is distributed under the terms of the GNU General Public
# 013358.python.hook-fastparquet.line5.comment License (version 2.0 or later).
# 013359.python.hook-fastparquet.line6.comment
# 013360.python.hook-fastparquet.line7.comment The full license is available in LICENSE, distributed with
# 013361.python.hook-fastparquet.line8.comment this software.
# 013362.python.hook-fastparquet.line9.comment
# 013363.python.hook-fastparquet.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013364.python.hook-fastparquet.line11.comment ------------------------------------------------------------------
import os

from PyInstaller.compat import is_win
from PyInstaller.utils.hooks import get_package_paths

# 013365.python.hook-fastparquet.line17.comment In all versions for which fastparquet provides Windows wheels (>= 0.7.0), delvewheel is used,
# 013366.python.hook-fastparquet.line18.comment so we need to collect the external site-packages/fastparquet.libs directory.
if is_win:
    pkg_base, pkg_dir = get_package_paths("fastparquet")
    lib_dir = os.path.join(pkg_base, "fastparquet.libs")
    if os.path.isdir(lib_dir):
        # 013367.python.hook-fastparquet.line23.comment We collect DLLs as data files instead of binaries to suppress binary
        # 013368.python.hook-fastparquet.line24.comment analysis, which would result in duplicates (because it collects a copy
        # 013369.python.hook-fastparquet.line25.comment into the top-level directory instead of preserving the original layout).
        # 013370.python.hook-fastparquet.line26.comment In addition to DLls, this also collects .load-order* file (required on
        # 013371.python.hook-fastparquet.line27.comment python < 3.8), and ensures that fastparquet.libs directory exists (required
        # 013372.python.hook-fastparquet.line28.comment on python >= 3.8 due to os.add_dll_directory call).
        datas = [
            (os.path.join(lib_dir, lib_file), 'fastparquet.libs')
            for lib_file in os.listdir(lib_dir)
        ]
