# 015005.python.hook-nvidia.curand.line1.comment ------------------------------------------------------------------
# 015006.python.hook-nvidia.curand.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 015007.python.hook-nvidia.curand.line3.comment
# 015008.python.hook-nvidia.curand.line4.comment This file is distributed under the terms of the GNU General Public
# 015009.python.hook-nvidia.curand.line5.comment License (version 2.0 or later).
# 015010.python.hook-nvidia.curand.line6.comment
# 015011.python.hook-nvidia.curand.line7.comment The full license is available in LICENSE, distributed with
# 015012.python.hook-nvidia.curand.line8.comment this software.
# 015013.python.hook-nvidia.curand.line9.comment
# 015014.python.hook-nvidia.curand.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015015.python.hook-nvidia.curand.line11.comment ------------------------------------------------------------------

from _pyinstaller_hooks_contrib.utils.nvidia_cuda import (
    collect_nvidia_cuda_binaries,
    create_symlink_suppression_patterns,
)

binaries = collect_nvidia_cuda_binaries(__file__)
bindepend_symlink_suppression = create_symlink_suppression_patterns(__file__)
