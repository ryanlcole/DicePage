# 015016.python.hook-nvidia.cusolver.line1.comment ------------------------------------------------------------------
# 015017.python.hook-nvidia.cusolver.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 015018.python.hook-nvidia.cusolver.line3.comment
# 015019.python.hook-nvidia.cusolver.line4.comment This file is distributed under the terms of the GNU General Public
# 015020.python.hook-nvidia.cusolver.line5.comment License (version 2.0 or later).
# 015021.python.hook-nvidia.cusolver.line6.comment
# 015022.python.hook-nvidia.cusolver.line7.comment The full license is available in LICENSE, distributed with
# 015023.python.hook-nvidia.cusolver.line8.comment this software.
# 015024.python.hook-nvidia.cusolver.line9.comment
# 015025.python.hook-nvidia.cusolver.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015026.python.hook-nvidia.cusolver.line11.comment ------------------------------------------------------------------

from _pyinstaller_hooks_contrib.utils.nvidia_cuda import (
    collect_nvidia_cuda_binaries,
    create_symlink_suppression_patterns,
)

binaries = collect_nvidia_cuda_binaries(__file__)
bindepend_symlink_suppression = create_symlink_suppression_patterns(__file__)
