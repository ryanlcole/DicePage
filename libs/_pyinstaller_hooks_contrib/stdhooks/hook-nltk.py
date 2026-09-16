# 014830.python.hook-nltk.line1.comment ------------------------------------------------------------------
# 014831.python.hook-nltk.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014832.python.hook-nltk.line3.comment
# 014833.python.hook-nltk.line4.comment This file is distributed under the terms of the GNU General Public
# 014834.python.hook-nltk.line5.comment License (version 2.0 or later).
# 014835.python.hook-nltk.line6.comment
# 014836.python.hook-nltk.line7.comment The full license is available in LICENSE, distributed with
# 014837.python.hook-nltk.line8.comment this software.
# 014838.python.hook-nltk.line9.comment
# 014839.python.hook-nltk.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014840.python.hook-nltk.line11.comment ------------------------------------------------------------------

# 014841.python.hook-nltk.line13.comment hook for nltk
import nltk
import os
from PyInstaller.utils.hooks import collect_data_files

# 014842.python.hook-nltk.line18.comment add datas for nltk
datas = collect_data_files('nltk', False)

# 014843.python.hook-nltk.line21.comment loop through the data directories and add them
for p in nltk.data.path:
    if os.path.exists(p):
        datas.append((p, "nltk_data"))

# 014844.python.hook-nltk.line26.comment nltk.chunk.named_entity should be included
hiddenimports = ["nltk.chunk.named_entity"]
