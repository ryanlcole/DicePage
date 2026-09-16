# 014983.python.hook-nvidia.cudnn.line1.comment ------------------------------------------------------------------
# 014984.python.hook-nvidia.cudnn.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 014985.python.hook-nvidia.cudnn.line3.comment
# 014986.python.hook-nvidia.cudnn.line4.comment This file is distributed under the terms of the GNU General Public
# 014987.python.hook-nvidia.cudnn.line5.comment License (version 2.0 or later).
# 014988.python.hook-nvidia.cudnn.line6.comment
# 014989.python.hook-nvidia.cudnn.line7.comment The full license is available in LICENSE, distributed with
# 014990.python.hook-nvidia.cudnn.line8.comment this software.
# 014991.python.hook-nvidia.cudnn.line9.comment
# 014992.python.hook-nvidia.cudnn.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014993.python.hook-nvidia.cudnn.line11.comment ------------------------------------------------------------------

from _pyinstaller_hooks_contrib.utils.nvidia_cuda import (
    collect_nvidia_cuda_binaries,
    create_symlink_suppression_patterns,
)

binaries = collect_nvidia_cuda_binaries(__file__)
bindepend_symlink_suppression = create_symlink_suppression_patterns(__file__)
