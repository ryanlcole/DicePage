# 014921.python.hook-nvidia.cublas.line1.comment ------------------------------------------------------------------
# 014922.python.hook-nvidia.cublas.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 014923.python.hook-nvidia.cublas.line3.comment
# 014924.python.hook-nvidia.cublas.line4.comment This file is distributed under the terms of the GNU General Public
# 014925.python.hook-nvidia.cublas.line5.comment License (version 2.0 or later).
# 014926.python.hook-nvidia.cublas.line6.comment
# 014927.python.hook-nvidia.cublas.line7.comment The full license is available in LICENSE, distributed with
# 014928.python.hook-nvidia.cublas.line8.comment this software.
# 014929.python.hook-nvidia.cublas.line9.comment
# 014930.python.hook-nvidia.cublas.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014931.python.hook-nvidia.cublas.line11.comment ------------------------------------------------------------------

from _pyinstaller_hooks_contrib.utils.nvidia_cuda import (
    collect_nvidia_cuda_binaries,
    create_symlink_suppression_patterns,
)

binaries = collect_nvidia_cuda_binaries(__file__)
bindepend_symlink_suppression = create_symlink_suppression_patterns(__file__)
