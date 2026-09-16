# 016512.python.hook-rtree.line1.comment ------------------------------------------------------------------
# 016513.python.hook-rtree.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 016514.python.hook-rtree.line3.comment
# 016515.python.hook-rtree.line4.comment This file is distributed under the terms of the GNU General Public
# 016516.python.hook-rtree.line5.comment License (version 2.0 or later).
# 016517.python.hook-rtree.line6.comment
# 016518.python.hook-rtree.line7.comment The full license is available in LICENSE, distributed with
# 016519.python.hook-rtree.line8.comment this software.
# 016520.python.hook-rtree.line9.comment
# 016521.python.hook-rtree.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016522.python.hook-rtree.line11.comment ------------------------------------------------------------------

import pathlib

from PyInstaller import compat
from PyInstaller.utils.hooks import collect_dynamic_libs, get_installer, get_package_paths


# 016523.python.hook-rtree.line19.comment Query the installer of the `rtree` package; in PyInstaller prior to 6.0, this might raise an exception, whereas in
# 016524.python.hook-rtree.line20.comment later versions, None is returned.
try:
    package_installer = get_installer('rtree')
except Exception:
    package_installer = None

if package_installer == 'conda':
    from PyInstaller.utils.hooks import conda

    # 016525.python.hook-rtree.line29.comment In Anaconda-packaged `rtree`, `libspatialindex` and `libspatialindex_c` shared libs are packaged in a separate
    # 016526.python.hook-rtree.line30.comment `libspatialindex` package. Collect the libraries into `rtree/lib` sub-directory to simulate PyPI wheel layout.
    binaries = conda.collect_dynamic_libs('libspatialindex', dest='rtree/lib', dependencies=False)
else:
    # 016527.python.hook-rtree.line33.comment pip-installed package. The shared libs are usually placed in `rtree/lib` directory.
    binaries = collect_dynamic_libs('rtree')

    # 016528.python.hook-rtree.line36.comment With rtree >= 1.1.0, Linux PyPI wheels place the shared library in a `Rtree.libs` top-level directory.
    # 016529.python.hook-rtree.line37.comment In rtree 1.4.0, the directory was renamed to `rtree.libs`
    if compat.is_linux:
        _, rtree_dir = get_package_paths('rtree')
        for candidate_dir_name in ('rtree.libs', 'Rtree.libs'):
            rtree_libs_dir = pathlib.Path(rtree_dir).parent / candidate_dir_name
            if not rtree_libs_dir.is_dir():
                continue
            binaries += [
                (str(lib_file), candidate_dir_name) for lib_file in rtree_libs_dir.glob("libspatialindex*.so*")
            ]
