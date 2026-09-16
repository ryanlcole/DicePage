# 018255.python.hook-urllib3_future.line1.comment ------------------------------------------------------------------
# 018256.python.hook-urllib3_future.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 018257.python.hook-urllib3_future.line3.comment
# 018258.python.hook-urllib3_future.line4.comment This file is distributed under the terms of the GNU General Public
# 018259.python.hook-urllib3_future.line5.comment License (version 2.0 or later).
# 018260.python.hook-urllib3_future.line6.comment
# 018261.python.hook-urllib3_future.line7.comment The full license is available in LICENSE, distributed with
# 018262.python.hook-urllib3_future.line8.comment this software.
# 018263.python.hook-urllib3_future.line9.comment
# 018264.python.hook-urllib3_future.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018265.python.hook-urllib3_future.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

# 018266.python.hook-urllib3_future.line15.comment Collect submodules in order to avoid missing modules due to indirect imports.
hiddenimports = collect_submodules("urllib3_future")
