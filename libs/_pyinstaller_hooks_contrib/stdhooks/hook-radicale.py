# 016383.python.hook-radicale.line1.comment ------------------------------------------------------------------
# 016384.python.hook-radicale.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016385.python.hook-radicale.line3.comment
# 016386.python.hook-radicale.line4.comment This file is distributed under the terms of the GNU General Public
# 016387.python.hook-radicale.line5.comment License (version 2.0 or later).
# 016388.python.hook-radicale.line6.comment
# 016389.python.hook-radicale.line7.comment The full license is available in LICENSE, distributed with
# 016390.python.hook-radicale.line8.comment this software.
# 016391.python.hook-radicale.line9.comment
# 016392.python.hook-radicale.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016393.python.hook-radicale.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import copy_metadata, collect_data_files

datas = copy_metadata('radicale')
datas += collect_data_files('radicale')
