# 012125.python.hook-av.line1.comment ------------------------------------------------------------------
# 012126.python.hook-av.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012127.python.hook-av.line3.comment
# 012128.python.hook-av.line4.comment This file is distributed under the terms of the GNU General Public
# 012129.python.hook-av.line5.comment License (version 2.0 or later).
# 012130.python.hook-av.line6.comment
# 012131.python.hook-av.line7.comment The full license is available in LICENSE, distributed with
# 012132.python.hook-av.line8.comment this software.
# 012133.python.hook-av.line9.comment
# 012134.python.hook-av.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012135.python.hook-av.line11.comment ------------------------------------------------------------------
import os

from PyInstaller.compat import is_win
from PyInstaller.utils.hooks import collect_submodules, is_module_satisfies, get_package_paths

hiddenimports = ['fractions'] + collect_submodules("av")

# 012136.python.hook-av.line19.comment Starting with av 9.1.1, the DLLs shipped with Windows PyPI wheels are stored
# 012137.python.hook-av.line20.comment in site-packages/av.libs instead of directly in the site-packages/av.
if is_module_satisfies("av >= 9.1.1") and is_win:
    pkg_base, pkg_dir = get_package_paths("av")
    lib_dir = os.path.join(pkg_base, "av.libs")
    if os.path.isdir(lib_dir):
        # 012138.python.hook-av.line25.comment We collect DLLs as data files instead of binaries to suppress binary
        # 012139.python.hook-av.line26.comment analysis, which would result in duplicates (because it collects a copy
        # 012140.python.hook-av.line27.comment into the top-level directory instead of preserving the original layout).
        # 012141.python.hook-av.line28.comment In addition to DLls, this also collects .load-order* file (required on
        # 012142.python.hook-av.line29.comment python < 3.8), and ensures that Shapely.libs directory exists (required
        # 012143.python.hook-av.line30.comment on python >= 3.8 due to os.add_dll_directory call).
        datas = [
            (os.path.join(lib_dir, lib_file), 'av.libs')
            for lib_file in os.listdir(lib_dir)
        ]

# 012144.python.hook-av.line36.comment With av 13.0.0, one of the cythonized modules (`av.audio.layout`) started using `dataclasses`. Add it to hidden
# 012145.python.hook-av.line37.comment imports to ensure it is collected in cases when it is not referenced from anywhere else.
if is_module_satisfies("av >= 13.0.0"):
    hiddenimports += ['dataclasses']

# 012146.python.hook-av.line41.comment av 13.1.0 added a cythonized `av.opaque` module that uses `uuid`; add it to hidden imports to ensure it is collected
# 012147.python.hook-av.line42.comment in cases when it is not referenced from anywhere else.
if is_module_satisfies("av >= 13.1.0"):
    hiddenimports += ['uuid']
