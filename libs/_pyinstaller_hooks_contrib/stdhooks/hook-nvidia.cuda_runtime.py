# 014972.python.hook-nvidia.cuda_runtime.line1.comment ------------------------------------------------------------------
# 014973.python.hook-nvidia.cuda_runtime.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 014974.python.hook-nvidia.cuda_runtime.line3.comment
# 014975.python.hook-nvidia.cuda_runtime.line4.comment This file is distributed under the terms of the GNU General Public
# 014976.python.hook-nvidia.cuda_runtime.line5.comment License (version 2.0 or later).
# 014977.python.hook-nvidia.cuda_runtime.line6.comment
# 014978.python.hook-nvidia.cuda_runtime.line7.comment The full license is available in LICENSE, distributed with
# 014979.python.hook-nvidia.cuda_runtime.line8.comment this software.
# 014980.python.hook-nvidia.cuda_runtime.line9.comment
# 014981.python.hook-nvidia.cuda_runtime.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014982.python.hook-nvidia.cuda_runtime.line11.comment ------------------------------------------------------------------

from _pyinstaller_hooks_contrib.utils.nvidia_cuda import (
    collect_nvidia_cuda_binaries,
    create_symlink_suppression_patterns,
)

binaries = collect_nvidia_cuda_binaries(__file__)
bindepend_symlink_suppression = create_symlink_suppression_patterns(__file__)
