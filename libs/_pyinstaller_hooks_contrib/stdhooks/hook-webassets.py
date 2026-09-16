# 020056.python.hook-webassets.line1.comment ------------------------------------------------------------------
# 020057.python.hook-webassets.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 020058.python.hook-webassets.line3.comment
# 020059.python.hook-webassets.line4.comment This file is distributed under the terms of the GNU General Public
# 020060.python.hook-webassets.line5.comment License (version 2.0 or later).
# 020061.python.hook-webassets.line6.comment
# 020062.python.hook-webassets.line7.comment The full license is available in LICENSE, distributed with
# 020063.python.hook-webassets.line8.comment this software.
# 020064.python.hook-webassets.line9.comment
# 020065.python.hook-webassets.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 020066.python.hook-webassets.line11.comment ------------------------------------------------------------------
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('webassets', include_py_files=True)
