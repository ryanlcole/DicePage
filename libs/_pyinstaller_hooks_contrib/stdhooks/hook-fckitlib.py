# 013373.python.hook-fckitlib.line1.comment ------------------------------------------------------------------
# 013374.python.hook-fckitlib.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 013375.python.hook-fckitlib.line3.comment
# 013376.python.hook-fckitlib.line4.comment This file is distributed under the terms of the GNU General Public
# 013377.python.hook-fckitlib.line5.comment License (version 2.0 or later).
# 013378.python.hook-fckitlib.line6.comment
# 013379.python.hook-fckitlib.line7.comment The full license is available in LICENSE, distributed with
# 013380.python.hook-fckitlib.line8.comment this software.
# 013381.python.hook-fckitlib.line9.comment
# 013382.python.hook-fckitlib.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013383.python.hook-fckitlib.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_dynamic_libs

# 013384.python.hook-fckitlib.line15.comment Collect bundled dynamic libraries.
binaries = collect_dynamic_libs('fckitlib')
