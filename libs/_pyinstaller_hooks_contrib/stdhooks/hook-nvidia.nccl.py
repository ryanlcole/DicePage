# 015038.python.hook-nvidia.nccl.line1.comment ------------------------------------------------------------------
# 015039.python.hook-nvidia.nccl.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 015040.python.hook-nvidia.nccl.line3.comment
# 015041.python.hook-nvidia.nccl.line4.comment This file is distributed under the terms of the GNU General Public
# 015042.python.hook-nvidia.nccl.line5.comment License (version 2.0 or later).
# 015043.python.hook-nvidia.nccl.line6.comment
# 015044.python.hook-nvidia.nccl.line7.comment The full license is available in LICENSE, distributed with
# 015045.python.hook-nvidia.nccl.line8.comment this software.
# 015046.python.hook-nvidia.nccl.line9.comment
# 015047.python.hook-nvidia.nccl.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015048.python.hook-nvidia.nccl.line11.comment ------------------------------------------------------------------

from _pyinstaller_hooks_contrib.utils.nvidia_cuda import (
    collect_nvidia_cuda_binaries,
    create_symlink_suppression_patterns,
)

binaries = collect_nvidia_cuda_binaries(__file__)
bindepend_symlink_suppression = create_symlink_suppression_patterns(__file__)
