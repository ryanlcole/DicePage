# 015049.python.hook-nvidia.nvjitlink.line1.comment ------------------------------------------------------------------
# 015050.python.hook-nvidia.nvjitlink.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 015051.python.hook-nvidia.nvjitlink.line3.comment
# 015052.python.hook-nvidia.nvjitlink.line4.comment This file is distributed under the terms of the GNU General Public
# 015053.python.hook-nvidia.nvjitlink.line5.comment License (version 2.0 or later).
# 015054.python.hook-nvidia.nvjitlink.line6.comment
# 015055.python.hook-nvidia.nvjitlink.line7.comment The full license is available in LICENSE, distributed with
# 015056.python.hook-nvidia.nvjitlink.line8.comment this software.
# 015057.python.hook-nvidia.nvjitlink.line9.comment
# 015058.python.hook-nvidia.nvjitlink.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015059.python.hook-nvidia.nvjitlink.line11.comment ------------------------------------------------------------------

from _pyinstaller_hooks_contrib.utils.nvidia_cuda import (
    collect_nvidia_cuda_binaries,
    create_symlink_suppression_patterns,
)

binaries = collect_nvidia_cuda_binaries(__file__)
bindepend_symlink_suppression = create_symlink_suppression_patterns(__file__)
