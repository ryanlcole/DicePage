# 017289.python.hook-stdnum.line1.comment ------------------------------------------------------------------
# 017290.python.hook-stdnum.line2.comment Copyright (c) 2022 PyInstaller Development Team.
# 017291.python.hook-stdnum.line3.comment
# 017292.python.hook-stdnum.line4.comment This file is distributed under the terms of the GNU General Public
# 017293.python.hook-stdnum.line5.comment License (version 2.0 or later).
# 017294.python.hook-stdnum.line6.comment
# 017295.python.hook-stdnum.line7.comment The full license is available in LICENSE, distributed with
# 017296.python.hook-stdnum.line8.comment this software.
# 017297.python.hook-stdnum.line9.comment
# 017298.python.hook-stdnum.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017299.python.hook-stdnum.line11.comment ------------------------------------------------------------------

# 017300.python.hook-stdnum.line13.comment Collect data files that are required by some of the stdnum's sub-modules
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("stdnum")
