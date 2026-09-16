# 015466.python.hook-pubsub.core.line1.comment ------------------------------------------------------------------
# 015467.python.hook-pubsub.core.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 015468.python.hook-pubsub.core.line3.comment
# 015469.python.hook-pubsub.core.line4.comment This file is distributed under the terms of the GNU General Public
# 015470.python.hook-pubsub.core.line5.comment License (version 2.0 or later).
# 015471.python.hook-pubsub.core.line6.comment
# 015472.python.hook-pubsub.core.line7.comment The full license is available in LICENSE, distributed with
# 015473.python.hook-pubsub.core.line8.comment this software.
# 015474.python.hook-pubsub.core.line9.comment
# 015475.python.hook-pubsub.core.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015476.python.hook-pubsub.core.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('pubsub.core', include_py_files=True, excludes=['*.txt', '**/__pycache__'])
