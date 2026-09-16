# 012007.python.hook-appy.pod.line1.comment ------------------------------------------------------------------
# 012008.python.hook-appy.pod.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012009.python.hook-appy.pod.line3.comment
# 012010.python.hook-appy.pod.line4.comment This file is distributed under the terms of the GNU General Public
# 012011.python.hook-appy.pod.line5.comment License (version 2.0 or later).
# 012012.python.hook-appy.pod.line6.comment
# 012013.python.hook-appy.pod.line7.comment The full license is available in LICENSE, distributed with
# 012014.python.hook-appy.pod.line8.comment this software.
# 012015.python.hook-appy.pod.line9.comment
# 012016.python.hook-appy.pod.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012017.python.hook-appy.pod.line11.comment ------------------------------------------------------------------

# 012018.python.hook-appy.pod.line13.comment Hook for appy.pod: https://pypi.python.org/pypi/appy/0.9.1

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('appy.pod', True)
