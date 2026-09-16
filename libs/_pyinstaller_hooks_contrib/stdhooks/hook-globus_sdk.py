# 013592.python.hook-globus_sdk.line1.comment ------------------------------------------------------------------
# 013593.python.hook-globus_sdk.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 013594.python.hook-globus_sdk.line3.comment
# 013595.python.hook-globus_sdk.line4.comment This file is distributed under the terms of the GNU General Public
# 013596.python.hook-globus_sdk.line5.comment License (version 2.0 or later).
# 013597.python.hook-globus_sdk.line6.comment
# 013598.python.hook-globus_sdk.line7.comment The full license is available in LICENSE, distributed with
# 013599.python.hook-globus_sdk.line8.comment this software.
# 013600.python.hook-globus_sdk.line9.comment
# 013601.python.hook-globus_sdk.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013602.python.hook-globus_sdk.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

datas = copy_metadata("globus_sdk")
datas += collect_data_files("globus_sdk")
hiddenimports = collect_submodules("globus_sdk")
