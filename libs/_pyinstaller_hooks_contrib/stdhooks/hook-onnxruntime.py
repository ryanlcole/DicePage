# 015082.python.hook-onnxruntime.line1.comment ------------------------------------------------------------------
# 015083.python.hook-onnxruntime.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 015084.python.hook-onnxruntime.line3.comment
# 015085.python.hook-onnxruntime.line4.comment This file is distributed under the terms of the GNU General Public
# 015086.python.hook-onnxruntime.line5.comment License (version 2.0 or later).
# 015087.python.hook-onnxruntime.line6.comment
# 015088.python.hook-onnxruntime.line7.comment The full license is available in LICENSE, distributed with
# 015089.python.hook-onnxruntime.line8.comment this software.
# 015090.python.hook-onnxruntime.line9.comment
# 015091.python.hook-onnxruntime.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015092.python.hook-onnxruntime.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_dynamic_libs

# 015093.python.hook-onnxruntime.line15.comment Collect provider plugins from onnxruntime/capi.
binaries = collect_dynamic_libs("onnxruntime")
