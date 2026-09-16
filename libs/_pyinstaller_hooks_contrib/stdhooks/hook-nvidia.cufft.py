# 014994.python.hook-nvidia.cufft.line1.comment ------------------------------------------------------------------
# 014995.python.hook-nvidia.cufft.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 014996.python.hook-nvidia.cufft.line3.comment
# 014997.python.hook-nvidia.cufft.line4.comment This file is distributed under the terms of the GNU General Public
# 014998.python.hook-nvidia.cufft.line5.comment License (version 2.0 or later).
# 014999.python.hook-nvidia.cufft.line6.comment
# 015000.python.hook-nvidia.cufft.line7.comment The full license is available in LICENSE, distributed with
# 015001.python.hook-nvidia.cufft.line8.comment this software.
# 015002.python.hook-nvidia.cufft.line9.comment
# 015003.python.hook-nvidia.cufft.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015004.python.hook-nvidia.cufft.line11.comment ------------------------------------------------------------------

from _pyinstaller_hooks_contrib.utils.nvidia_cuda import (
    collect_nvidia_cuda_binaries,
    create_symlink_suppression_patterns,
)

binaries = collect_nvidia_cuda_binaries(__file__)
bindepend_symlink_suppression = create_symlink_suppression_patterns(__file__)
