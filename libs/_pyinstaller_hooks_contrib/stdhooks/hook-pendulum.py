# 015291.python.hook-pendulum.line1.comment ------------------------------------------------------------------
# 015292.python.hook-pendulum.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 015293.python.hook-pendulum.line3.comment
# 015294.python.hook-pendulum.line4.comment This file is distributed under the terms of the GNU General Public
# 015295.python.hook-pendulum.line5.comment License (version 2.0 or later).
# 015296.python.hook-pendulum.line6.comment
# 015297.python.hook-pendulum.line7.comment The full license is available in LICENSE, distributed with
# 015298.python.hook-pendulum.line8.comment this software.
# 015299.python.hook-pendulum.line9.comment
# 015300.python.hook-pendulum.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015301.python.hook-pendulum.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 015302.python.hook-pendulum.line15.comment Pendulum checks for locale modules via os.path.exists before import.
# 015303.python.hook-pendulum.line16.comment If the include_py_files option is turned off, this check fails, pendulum
# 015304.python.hook-pendulum.line17.comment will raise a ValueError.
datas = collect_data_files("pendulum.locales", include_py_files=True)
hiddenimports = collect_submodules("pendulum.locales")
