# 017491.python.hook-thinc.line1.comment ------------------------------------------------------------------
# 017492.python.hook-thinc.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 017493.python.hook-thinc.line3.comment
# 017494.python.hook-thinc.line4.comment This file is distributed under the terms of the GNU General Public
# 017495.python.hook-thinc.line5.comment License (version 2.0 or later).
# 017496.python.hook-thinc.line6.comment
# 017497.python.hook-thinc.line7.comment The full license is available in LICENSE, distributed with
# 017498.python.hook-thinc.line8.comment this software.
# 017499.python.hook-thinc.line9.comment
# 017500.python.hook-thinc.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017501.python.hook-thinc.line11.comment ------------------------------------------------------------------
"""
Thinc contains data files and hidden imports. This hook was created to make spacy work correctly.
"""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = collect_data_files("thinc")
hiddenimports = collect_submodules("thinc")
