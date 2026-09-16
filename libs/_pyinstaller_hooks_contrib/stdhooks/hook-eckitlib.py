# 013074.python.hook-eckitlib.line1.comment ------------------------------------------------------------------
# 013075.python.hook-eckitlib.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 013076.python.hook-eckitlib.line3.comment
# 013077.python.hook-eckitlib.line4.comment This file is distributed under the terms of the GNU General Public
# 013078.python.hook-eckitlib.line5.comment License (version 2.0 or later).
# 013079.python.hook-eckitlib.line6.comment
# 013080.python.hook-eckitlib.line7.comment The full license is available in LICENSE, distributed with
# 013081.python.hook-eckitlib.line8.comment this software.
# 013082.python.hook-eckitlib.line9.comment
# 013083.python.hook-eckitlib.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013084.python.hook-eckitlib.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_dynamic_libs

# 013085.python.hook-eckitlib.line15.comment Collect bundled dynamic libraries.
binaries = collect_dynamic_libs('eckitlib')
