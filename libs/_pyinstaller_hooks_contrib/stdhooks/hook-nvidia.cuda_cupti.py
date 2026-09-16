# 014932.python.hook-nvidia.cuda_cupti.line1.comment ------------------------------------------------------------------
# 014933.python.hook-nvidia.cuda_cupti.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 014934.python.hook-nvidia.cuda_cupti.line3.comment
# 014935.python.hook-nvidia.cuda_cupti.line4.comment This file is distributed under the terms of the GNU General Public
# 014936.python.hook-nvidia.cuda_cupti.line5.comment License (version 2.0 or later).
# 014937.python.hook-nvidia.cuda_cupti.line6.comment
# 014938.python.hook-nvidia.cuda_cupti.line7.comment The full license is available in LICENSE, distributed with
# 014939.python.hook-nvidia.cuda_cupti.line8.comment this software.
# 014940.python.hook-nvidia.cuda_cupti.line9.comment
# 014941.python.hook-nvidia.cuda_cupti.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014942.python.hook-nvidia.cuda_cupti.line11.comment ------------------------------------------------------------------

from _pyinstaller_hooks_contrib.utils.nvidia_cuda import (
    collect_nvidia_cuda_binaries,
    create_symlink_suppression_patterns,
)

binaries = collect_nvidia_cuda_binaries(__file__)
bindepend_symlink_suppression = create_symlink_suppression_patterns(__file__)
