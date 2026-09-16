# 018107.python.hook-triton.line1.comment ------------------------------------------------------------------
# 018108.python.hook-triton.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 018109.python.hook-triton.line3.comment
# 018110.python.hook-triton.line4.comment This file is distributed under the terms of the GNU General Public
# 018111.python.hook-triton.line5.comment License (version 2.0 or later).
# 018112.python.hook-triton.line6.comment
# 018113.python.hook-triton.line7.comment The full license is available in LICENSE, distributed with
# 018114.python.hook-triton.line8.comment this software.
# 018115.python.hook-triton.line9.comment
# 018116.python.hook-triton.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018117.python.hook-triton.line11.comment ---------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules, is_module_satisfies

hiddenimports = []
datas = []

# 018118.python.hook-triton.line18.comment Ensure that triton/_C/libtriton.so is collected
binaries = collect_dynamic_libs('triton')

# 018119.python.hook-triton.line21.comment triton has a JIT module that requires its source .py files. For some god-forsaken reason, this JIT module
# 018120.python.hook-triton.line22.comment (`triton.runtime.jit` attempts to directly read the contents of file pointed to by its `__file__` attribute (assuming
# 018121.python.hook-triton.line23.comment it is a source file). Therefore, `triton.runtime.jit` must not be collected into PYZ. Same goes for `compiler` and
# 018122.python.hook-triton.line24.comment `language` sub-packages.
module_collection_mode = {
    'triton': 'pyz+py',
    'triton.runtime.jit': 'py',
    'triton.compiler': 'py',
    'triton.language': 'py',
}

# 018123.python.hook-triton.line32.comment triton 3.0.0 introduced `triton.backends` sub-package with backend-specific files.
if is_module_satisfies('triton >= 3.0.0'):
    # 018124.python.hook-triton.line34.comment Collect backend sub-modules/packages.
    hiddenimports += collect_submodules('triton.backends')

    # 018125.python.hook-triton.line37.comment At the time of writing (triton v3.1.0), `triton.backends.amd` is a namespace package, and is not captured by the
    # 018126.python.hook-triton.line38.comment above `collect_submodules` call.
    hiddenimports += collect_submodules('triton.backends.amd')

    # 018127.python.hook-triton.line41.comment Collect ptxas compiler files from `triton/backends/nvidia`, and the HIP/ROCm files from `triton/backends/amd`.
    datas += collect_data_files('triton.backends')
else:
    # 018128.python.hook-triton.line44.comment Collect ptxas compiler files from triton/third_party/cuda directory. Strictly speaking, the ptxas executable from
    # 018129.python.hook-triton.line45.comment bin directory should be collected as a binary, but in this case, it makes no difference (plus, PyInstaller >= 6.0
    # 018130.python.hook-triton.line46.comment has automatic binary-vs-data reclassification).
    datas += collect_data_files('triton.third_party.cuda')
