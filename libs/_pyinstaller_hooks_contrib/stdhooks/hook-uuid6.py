# 018297.python.hook-uuid6.line1.comment ------------------------------------------------------------------
# 018298.python.hook-uuid6.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 018299.python.hook-uuid6.line3.comment
# 018300.python.hook-uuid6.line4.comment This file is distributed under the terms of the GNU General Public
# 018301.python.hook-uuid6.line5.comment License (version 2.0 or later).
# 018302.python.hook-uuid6.line6.comment
# 018303.python.hook-uuid6.line7.comment The full license is available in LICENSE, distributed with
# 018304.python.hook-uuid6.line8.comment this software.
# 018305.python.hook-uuid6.line9.comment
# 018306.python.hook-uuid6.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018307.python.hook-uuid6.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies, copy_metadata

# 018308.python.hook-uuid6.line15.comment Starting with version 2025.0.1, uuid6 queries its metadata for version information.
if is_module_satisfies('uuid6 >= 2025.0.1'):
    datas = copy_metadata('uuid6')
