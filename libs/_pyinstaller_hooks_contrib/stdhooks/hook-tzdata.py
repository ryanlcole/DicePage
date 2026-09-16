# 018153.python.hook-tzdata.line1.comment ------------------------------------------------------------------
# 018154.python.hook-tzdata.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 018155.python.hook-tzdata.line3.comment
# 018156.python.hook-tzdata.line4.comment This file is distributed under the terms of the GNU General Public
# 018157.python.hook-tzdata.line5.comment License (version 2.0 or later).
# 018158.python.hook-tzdata.line6.comment
# 018159.python.hook-tzdata.line7.comment The full license is available in LICENSE, distributed with
# 018160.python.hook-tzdata.line8.comment this software.
# 018161.python.hook-tzdata.line9.comment
# 018162.python.hook-tzdata.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018163.python.hook-tzdata.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 018164.python.hook-tzdata.line15.comment Collect timezone data files
datas = collect_data_files("tzdata")

# 018165.python.hook-tzdata.line18.comment Collect submodules; each data subdirectory is in fact a package
# 018166.python.hook-tzdata.line19.comment (e.g., zoneinfo.Europe), so we need its __init__.py for data files
# 018167.python.hook-tzdata.line20.comment (e.g., zoneinfo/Europe/Ljubljana) to be discoverable via
# 018168.python.hook-tzdata.line21.comment importlib.resources
hiddenimports = collect_submodules("tzdata")
