# 016372.python.hook-qtmodern.line1.comment ------------------------------------------------------------------
# 016373.python.hook-qtmodern.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 016374.python.hook-qtmodern.line3.comment
# 016375.python.hook-qtmodern.line4.comment This file is distributed under the terms of the GNU General Public
# 016376.python.hook-qtmodern.line5.comment License (version 2.0 or later).
# 016377.python.hook-qtmodern.line6.comment
# 016378.python.hook-qtmodern.line7.comment The full license is available in LICENSE, distributed with
# 016379.python.hook-qtmodern.line8.comment this software.
# 016380.python.hook-qtmodern.line9.comment
# 016381.python.hook-qtmodern.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016382.python.hook-qtmodern.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("qtmodern", includes=["**/*.qss"])
