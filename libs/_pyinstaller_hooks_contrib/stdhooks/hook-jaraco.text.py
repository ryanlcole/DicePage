# 014029.python.hook-jaraco.text.line1.comment ------------------------------------------------------------------
# 014030.python.hook-jaraco.text.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014031.python.hook-jaraco.text.line3.comment
# 014032.python.hook-jaraco.text.line4.comment This file is distributed under the terms of the GNU General Public
# 014033.python.hook-jaraco.text.line5.comment License (version 2.0 or later).
# 014034.python.hook-jaraco.text.line6.comment
# 014035.python.hook-jaraco.text.line7.comment The full license is available in LICENSE, distributed with
# 014036.python.hook-jaraco.text.line8.comment this software.
# 014037.python.hook-jaraco.text.line9.comment
# 014038.python.hook-jaraco.text.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014039.python.hook-jaraco.text.line11.comment ------------------------------------------------------------------

# 014040.python.hook-jaraco.text.line13.comment Hook for jaraco: https://pypi.python.org/pypi/jaraco.text/3.2.0

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('jaraco.text')
