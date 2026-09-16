# 014280.python.hook-librosa.line1.comment ------------------------------------------------------------------
# 014281.python.hook-librosa.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 014282.python.hook-librosa.line3.comment
# 014283.python.hook-librosa.line4.comment This file is distributed under the terms of the GNU General Public
# 014284.python.hook-librosa.line5.comment License (version 2.0 or later).
# 014285.python.hook-librosa.line6.comment
# 014286.python.hook-librosa.line7.comment The full license is available in LICENSE, distributed with
# 014287.python.hook-librosa.line8.comment this software.
# 014288.python.hook-librosa.line9.comment
# 014289.python.hook-librosa.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014290.python.hook-librosa.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 014291.python.hook-librosa.line15.comment Collect all data files from the package. These include:
# 014292.python.hook-librosa.line16.comment - package's and subpackages' .pyi files for `lazy_loader`
# 014293.python.hook-librosa.line17.comment - example data in librosa/util, required by `librosa.util.files`
# 014294.python.hook-librosa.line18.comment - librosa/core/intervals.msgpack, required by `librosa.core.intervals`
# 014295.python.hook-librosa.line19.comment
# 014296.python.hook-librosa.line20.comment We explicitly exclude `__pycache__` because it might contain .nbi and .nbc files from `numba` cache, which are not
# 014297.python.hook-librosa.line21.comment re-used by `numba` codepaths in the frozen application and are instead re-compiled in user-global cache directory.
datas = collect_data_files("librosa", excludes=['**/__pycache__'])

# 014298.python.hook-librosa.line24.comment And because modules are lazily loaded, we need to collect them all.
hiddenimports = collect_submodules("librosa")
