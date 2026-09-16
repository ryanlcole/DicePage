# 012459.python.hook-celpy.line1.comment ------------------------------------------------------------------
# 012460.python.hook-celpy.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 012461.python.hook-celpy.line3.comment
# 012462.python.hook-celpy.line4.comment This file is distributed under the terms of the GNU General Public
# 012463.python.hook-celpy.line5.comment License (version 2.0 or later).
# 012464.python.hook-celpy.line6.comment
# 012465.python.hook-celpy.line7.comment The full license is available in LICENSE, distributed with
# 012466.python.hook-celpy.line8.comment this software.
# 012467.python.hook-celpy.line9.comment
# 012468.python.hook-celpy.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012469.python.hook-celpy.line11.comment ------------------------------------------------------------------
# 012470.python.hook-celpy.line12.comment
# 012471.python.hook-celpy.line13.comment cel-python is Pure Python implementation of Google Common Expression Language,
# 012472.python.hook-celpy.line14.comment https://opensource.google/projects/cel
# 012473.python.hook-celpy.line15.comment This implementation has minimal dependencies, runs quickly, and can be embedded into Python-based applications.
# 012474.python.hook-celpy.line16.comment Specifically, the intent is to be part of Cloud Custodian, C7N, as part of the security policy filter.
# 012475.python.hook-celpy.line17.comment https://github.com/cloud-custodian/cel-python
# 012476.python.hook-celpy.line18.comment
# 012477.python.hook-celpy.line19.comment Tested with cel-python 0.1.5

from PyInstaller.utils.hooks import collect_data_files

# 012478.python.hook-celpy.line23.comment Collect *.lark file(s) from the package
datas = collect_data_files('celpy')
