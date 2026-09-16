# 014004.python.hook-iso639.line1.comment ------------------------------------------------------------------
# 014005.python.hook-iso639.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 014006.python.hook-iso639.line3.comment
# 014007.python.hook-iso639.line4.comment This file is distributed under the terms of the GNU General Public
# 014008.python.hook-iso639.line5.comment License (version 2.0 or later).
# 014009.python.hook-iso639.line6.comment
# 014010.python.hook-iso639.line7.comment The full license is available in LICENSE, distributed with
# 014011.python.hook-iso639.line8.comment this software.
# 014012.python.hook-iso639.line9.comment
# 014013.python.hook-iso639.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014014.python.hook-iso639.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

# 014015.python.hook-iso639.line15.comment Collect data files for iso639
datas = collect_data_files("iso639")
