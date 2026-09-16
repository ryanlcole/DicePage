# 013432.python.hook-flex.line1.comment ------------------------------------------------------------------
# 013433.python.hook-flex.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 013434.python.hook-flex.line3.comment
# 013435.python.hook-flex.line4.comment This file is distributed under the terms of the GNU General Public
# 013436.python.hook-flex.line5.comment License (version 2.0 or later).
# 013437.python.hook-flex.line6.comment
# 013438.python.hook-flex.line7.comment The full license is available in LICENSE, distributed with
# 013439.python.hook-flex.line8.comment this software.
# 013440.python.hook-flex.line9.comment
# 013441.python.hook-flex.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013442.python.hook-flex.line11.comment ------------------------------------------------------------------

# 013443.python.hook-flex.line13.comment hook for https://github.com/pipermerriam/flex

from PyInstaller.utils.hooks import copy_metadata

datas = copy_metadata('flex')
