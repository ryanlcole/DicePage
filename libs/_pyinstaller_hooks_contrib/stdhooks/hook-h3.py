# 013846.python.hook-h3.line1.comment ------------------------------------------------------------------
# 013847.python.hook-h3.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 013848.python.hook-h3.line3.comment
# 013849.python.hook-h3.line4.comment This file is distributed under the terms of the GNU General Public
# 013850.python.hook-h3.line5.comment License (version 2.0 or later).
# 013851.python.hook-h3.line6.comment
# 013852.python.hook-h3.line7.comment The full license is available in LICENSE, distributed with
# 013853.python.hook-h3.line8.comment this software.
# 013854.python.hook-h3.line9.comment
# 013855.python.hook-h3.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013856.python.hook-h3.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies, copy_metadata

# 013857.python.hook-h3.line15.comment Starting with v4.0.0, h3 determines its version from its metadata.
if is_module_satisfies("h3 >= 4.0.0"):
    datas = copy_metadata("h3")
