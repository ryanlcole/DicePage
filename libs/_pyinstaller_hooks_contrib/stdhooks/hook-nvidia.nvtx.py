# 015060.python.hook-nvidia.nvtx.line1.comment ------------------------------------------------------------------
# 015061.python.hook-nvidia.nvtx.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 015062.python.hook-nvidia.nvtx.line3.comment
# 015063.python.hook-nvidia.nvtx.line4.comment This file is distributed under the terms of the GNU General Public
# 015064.python.hook-nvidia.nvtx.line5.comment License (version 2.0 or later).
# 015065.python.hook-nvidia.nvtx.line6.comment
# 015066.python.hook-nvidia.nvtx.line7.comment The full license is available in LICENSE, distributed with
# 015067.python.hook-nvidia.nvtx.line8.comment this software.
# 015068.python.hook-nvidia.nvtx.line9.comment
# 015069.python.hook-nvidia.nvtx.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015070.python.hook-nvidia.nvtx.line11.comment ------------------------------------------------------------------

from _pyinstaller_hooks_contrib.utils.nvidia_cuda import (
    collect_nvidia_cuda_binaries,
    create_symlink_suppression_patterns,
)

binaries = collect_nvidia_cuda_binaries(__file__)
bindepend_symlink_suppression = create_symlink_suppression_patterns(__file__)
