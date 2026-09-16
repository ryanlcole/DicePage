# 017468.python.hook-textdistance.line1.comment ------------------------------------------------------------------
# 017469.python.hook-textdistance.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 017470.python.hook-textdistance.line3.comment
# 017471.python.hook-textdistance.line4.comment This file is distributed under the terms of the GNU General Public
# 017472.python.hook-textdistance.line5.comment License (version 2.0 or later).
# 017473.python.hook-textdistance.line6.comment
# 017474.python.hook-textdistance.line7.comment The full license is available in LICENSE, distributed with
# 017475.python.hook-textdistance.line8.comment this software.
# 017476.python.hook-textdistance.line9.comment
# 017477.python.hook-textdistance.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017478.python.hook-textdistance.line11.comment ------------------------------------------------------------------

# 017479.python.hook-textdistance.line13.comment Hook for textdistance: https://pypi.org/project/textdistance/4.1.3/

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('textdistance')
