# 017456.python.hook-text_unidecode.line1.comment ------------------------------------------------------------------
# 017457.python.hook-text_unidecode.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 017458.python.hook-text_unidecode.line3.comment
# 017459.python.hook-text_unidecode.line4.comment This file is distributed under the terms of the GNU General Public
# 017460.python.hook-text_unidecode.line5.comment License (version 2.0 or later).
# 017461.python.hook-text_unidecode.line6.comment
# 017462.python.hook-text_unidecode.line7.comment The full license is available in LICENSE, distributed with
# 017463.python.hook-text_unidecode.line8.comment this software.
# 017464.python.hook-text_unidecode.line9.comment
# 017465.python.hook-text_unidecode.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017466.python.hook-text_unidecode.line11.comment ------------------------------------------------------------------
# 017467.python.hook-text_unidecode.line12.comment -----------------------------------------------------------------------------
"""
text-unidecode:
https://github.com/kmike/text-unidecode/
"""

import os
from PyInstaller.utils.hooks import get_package_paths

package_path = get_package_paths("text_unidecode")
data_bin_path = os.path.join(package_path[1], "data.bin")

if os.path.exists(data_bin_path):
    datas = [(data_bin_path, 'text_unidecode')]
