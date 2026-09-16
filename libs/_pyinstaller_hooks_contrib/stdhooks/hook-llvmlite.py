# 014379.python.hook-llvmlite.line1.comment ------------------------------------------------------------------
# 014380.python.hook-llvmlite.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014381.python.hook-llvmlite.line3.comment
# 014382.python.hook-llvmlite.line4.comment This file is distributed under the terms of the GNU General Public
# 014383.python.hook-llvmlite.line5.comment License (version 2.0 or later).
# 014384.python.hook-llvmlite.line6.comment
# 014385.python.hook-llvmlite.line7.comment The full license is available in LICENSE, distributed with
# 014386.python.hook-llvmlite.line8.comment this software.
# 014387.python.hook-llvmlite.line9.comment
# 014388.python.hook-llvmlite.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014389.python.hook-llvmlite.line11.comment ------------------------------------------------------------------
# 014390.python.hook-llvmlite.line12.comment
# 014391.python.hook-llvmlite.line13.comment A lightweight LLVM python binding for writing JIT compilers
# 014392.python.hook-llvmlite.line14.comment https://github.com/numba/llvmlite
# 014393.python.hook-llvmlite.line15.comment
# 014394.python.hook-llvmlite.line16.comment Tested with:
# 014395.python.hook-llvmlite.line17.comment llvmlite 0.11 (Anaconda 4.1.1, Windows), llvmlite 0.13 (Linux)

from PyInstaller.utils.hooks import collect_dynamic_libs

binaries = collect_dynamic_libs("llvmlite")
