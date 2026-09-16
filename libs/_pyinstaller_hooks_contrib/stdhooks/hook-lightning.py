# 014320.python.hook-lightning.line1.comment ------------------------------------------------------------------
# 014321.python.hook-lightning.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 014322.python.hook-lightning.line3.comment
# 014323.python.hook-lightning.line4.comment This file is distributed under the terms of the GNU General Public
# 014324.python.hook-lightning.line5.comment License (version 2.0 or later).
# 014325.python.hook-lightning.line6.comment
# 014326.python.hook-lightning.line7.comment The full license is available in LICENSE, distributed with
# 014327.python.hook-lightning.line8.comment this software.
# 014328.python.hook-lightning.line9.comment
# 014329.python.hook-lightning.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014330.python.hook-lightning.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

# 014331.python.hook-lightning.line15.comment Collect version.info (which is read during package import at run-time). Avoid collecting data from `lightning.app`,
# 014332.python.hook-lightning.line16.comment which likely does not work with PyInstaller without additional tricks (if we need to collect that data, it should
# 014333.python.hook-lightning.line17.comment be done in separate `lightning.app` hook).
datas = collect_data_files(
    'lightning',
    includes=['version.info'],
)
