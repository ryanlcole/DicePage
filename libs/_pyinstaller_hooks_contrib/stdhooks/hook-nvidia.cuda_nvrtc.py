# 014961.python.hook-nvidia.cuda_nvrtc.line1.comment ------------------------------------------------------------------
# 014962.python.hook-nvidia.cuda_nvrtc.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 014963.python.hook-nvidia.cuda_nvrtc.line3.comment
# 014964.python.hook-nvidia.cuda_nvrtc.line4.comment This file is distributed under the terms of the GNU General Public
# 014965.python.hook-nvidia.cuda_nvrtc.line5.comment License (version 2.0 or later).
# 014966.python.hook-nvidia.cuda_nvrtc.line6.comment
# 014967.python.hook-nvidia.cuda_nvrtc.line7.comment The full license is available in LICENSE, distributed with
# 014968.python.hook-nvidia.cuda_nvrtc.line8.comment this software.
# 014969.python.hook-nvidia.cuda_nvrtc.line9.comment
# 014970.python.hook-nvidia.cuda_nvrtc.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014971.python.hook-nvidia.cuda_nvrtc.line11.comment ------------------------------------------------------------------

from _pyinstaller_hooks_contrib.utils.nvidia_cuda import (
    collect_nvidia_cuda_binaries,
    create_symlink_suppression_patterns,
)

binaries = collect_nvidia_cuda_binaries(__file__)
bindepend_symlink_suppression = create_symlink_suppression_patterns(__file__)
