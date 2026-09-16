# 014481.python.hook-magic.line1.comment ------------------------------------------------------------------
# 014482.python.hook-magic.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014483.python.hook-magic.line3.comment
# 014484.python.hook-magic.line4.comment This file is distributed under the terms of the GNU General Public
# 014485.python.hook-magic.line5.comment License (version 2.0 or later).
# 014486.python.hook-magic.line6.comment
# 014487.python.hook-magic.line7.comment The full license is available in LICENSE, distributed with
# 014488.python.hook-magic.line8.comment this software.
# 014489.python.hook-magic.line9.comment
# 014490.python.hook-magic.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014491.python.hook-magic.line11.comment ------------------------------------------------------------------

# 014492.python.hook-magic.line13.comment hook for https://pypi.org/project/python-magic-bin

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

datas = collect_data_files('magic')
binaries = collect_dynamic_libs('magic')
