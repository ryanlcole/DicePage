# 013881.python.hook-hexbytes.line1.comment ------------------------------------------------------------------
# 013882.python.hook-hexbytes.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 013883.python.hook-hexbytes.line3.comment
# 013884.python.hook-hexbytes.line4.comment This file is distributed under the terms of the GNU General Public
# 013885.python.hook-hexbytes.line5.comment License (version 2.0 or later).
# 013886.python.hook-hexbytes.line6.comment
# 013887.python.hook-hexbytes.line7.comment The full license is available in LICENSE, distributed with
# 013888.python.hook-hexbytes.line8.comment this software.
# 013889.python.hook-hexbytes.line9.comment
# 013890.python.hook-hexbytes.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013891.python.hook-hexbytes.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies, copy_metadata

# 013892.python.hook-hexbytes.line15.comment Starting with v1.1.0, `hexbytes` queries its version from metadata.
if is_module_satisfies("hexbytes >= 1.1.0"):
    datas = copy_metadata('hexbytes')
