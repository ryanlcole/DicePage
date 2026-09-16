# 015027.python.hook-nvidia.cusparse.line1.comment ------------------------------------------------------------------
# 015028.python.hook-nvidia.cusparse.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 015029.python.hook-nvidia.cusparse.line3.comment
# 015030.python.hook-nvidia.cusparse.line4.comment This file is distributed under the terms of the GNU General Public
# 015031.python.hook-nvidia.cusparse.line5.comment License (version 2.0 or later).
# 015032.python.hook-nvidia.cusparse.line6.comment
# 015033.python.hook-nvidia.cusparse.line7.comment The full license is available in LICENSE, distributed with
# 015034.python.hook-nvidia.cusparse.line8.comment this software.
# 015035.python.hook-nvidia.cusparse.line9.comment
# 015036.python.hook-nvidia.cusparse.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015037.python.hook-nvidia.cusparse.line11.comment ------------------------------------------------------------------

from _pyinstaller_hooks_contrib.utils.nvidia_cuda import (
    collect_nvidia_cuda_binaries,
    create_symlink_suppression_patterns,
)

binaries = collect_nvidia_cuda_binaries(__file__)
bindepend_symlink_suppression = create_symlink_suppression_patterns(__file__)
