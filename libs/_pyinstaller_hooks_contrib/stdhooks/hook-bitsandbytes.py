# 012232.python.hook-bitsandbytes.line1.comment ------------------------------------------------------------------
# 012233.python.hook-bitsandbytes.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 012234.python.hook-bitsandbytes.line3.comment
# 012235.python.hook-bitsandbytes.line4.comment This file is distributed under the terms of the GNU General Public
# 012236.python.hook-bitsandbytes.line5.comment License (version 2.0 or later).
# 012237.python.hook-bitsandbytes.line6.comment
# 012238.python.hook-bitsandbytes.line7.comment The full license is available in LICENSE, distributed with
# 012239.python.hook-bitsandbytes.line8.comment this software.
# 012240.python.hook-bitsandbytes.line9.comment
# 012241.python.hook-bitsandbytes.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012242.python.hook-bitsandbytes.line11.comment ---------------------------------------------------

from PyInstaller.utils.hooks import collect_dynamic_libs

# 012243.python.hook-bitsandbytes.line15.comment bitsandbytes contains several extensions for CPU and different CUDA versions: libbitsandbytes_cpu.so,
# 012244.python.hook-bitsandbytes.line16.comment libbitsandbytes_cuda110_nocublaslt.so, libbitsandbytes_cuda110.so, etc. At build-time, we could query the
# 012245.python.hook-bitsandbytes.line17.comment `bitsandbytes.cextension.setup` and its `binary_name` attribute for the extension that is in use. However, if the
# 012246.python.hook-bitsandbytes.line18.comment build system does not have CUDA available, this would automatically mean that we will not collect any of the CUDA
# 012247.python.hook-bitsandbytes.line19.comment libs. So for now, we collect them all.
binaries = collect_dynamic_libs("bitsandbytes")

# 012248.python.hook-bitsandbytes.line22.comment bitsandbytes uses triton's JIT module, which requires access to source .py files.
module_collection_mode = 'pyz+py'
