# 014943.python.hook-nvidia.cuda_nvcc.line1.comment ------------------------------------------------------------------
# 014944.python.hook-nvidia.cuda_nvcc.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 014945.python.hook-nvidia.cuda_nvcc.line3.comment
# 014946.python.hook-nvidia.cuda_nvcc.line4.comment This file is distributed under the terms of the GNU General Public
# 014947.python.hook-nvidia.cuda_nvcc.line5.comment License (version 2.0 or later).
# 014948.python.hook-nvidia.cuda_nvcc.line6.comment
# 014949.python.hook-nvidia.cuda_nvcc.line7.comment The full license is available in LICENSE, distributed with
# 014950.python.hook-nvidia.cuda_nvcc.line8.comment this software.
# 014951.python.hook-nvidia.cuda_nvcc.line9.comment
# 014952.python.hook-nvidia.cuda_nvcc.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014953.python.hook-nvidia.cuda_nvcc.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files
from _pyinstaller_hooks_contrib.utils.nvidia_cuda import (
    collect_nvidia_cuda_binaries,
    create_symlink_suppression_patterns,
)

# 014954.python.hook-nvidia.cuda_nvcc.line19.comment Ensures that versioned .so files are collected
binaries = collect_nvidia_cuda_binaries(__file__)

# 014955.python.hook-nvidia.cuda_nvcc.line22.comment Prevent binary dependency analysis from creating symlinks to top-level application directory for shared libraries
# 014956.python.hook-nvidia.cuda_nvcc.line23.comment from this package. Requires PyInstaller >= 6.11.0; no-op in earlier versions.
bindepend_symlink_suppression = create_symlink_suppression_patterns(__file__)

# 014957.python.hook-nvidia.cuda_nvcc.line26.comment Collect additional resources:
# 014958.python.hook-nvidia.cuda_nvcc.line27.comment - ptxas executable (which strictly speaking, should be collected as a binary)
# 014959.python.hook-nvidia.cuda_nvcc.line28.comment - nvvm/libdevice/libdevice.10.bc file
# 014960.python.hook-nvidia.cuda_nvcc.line29.comment - C headers; assuming ptxas requires them - if that is not the case, we could filter them out.
datas = collect_data_files('nvidia.cuda_nvcc')
