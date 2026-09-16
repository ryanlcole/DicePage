# 015405.python.hook-prettytable.line1.comment ------------------------------------------------------------------
# 015406.python.hook-prettytable.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 015407.python.hook-prettytable.line3.comment
# 015408.python.hook-prettytable.line4.comment This file is distributed under the terms of the GNU General Public
# 015409.python.hook-prettytable.line5.comment License (version 2.0 or later).
# 015410.python.hook-prettytable.line6.comment
# 015411.python.hook-prettytable.line7.comment The full license is available in LICENSE, distributed with
# 015412.python.hook-prettytable.line8.comment this software.
# 015413.python.hook-prettytable.line9.comment
# 015414.python.hook-prettytable.line10.comment SPDX-License-Identifier GPL-2.0-or-later
# 015415.python.hook-prettytable.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import copy_metadata, is_module_satisfies

# 015416.python.hook-prettytable.line15.comment Starting with v3.12.0, `prettytable` does not query its version from metadata.
if is_module_satisfies('prettytable < 3.12.0'):
    datas = copy_metadata('prettytable')
