# 013490.python.hook-frictionless.line1.comment ------------------------------------------------------------------
# 013491.python.hook-frictionless.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 013492.python.hook-frictionless.line3.comment
# 013493.python.hook-frictionless.line4.comment This file is distributed under the terms of the GNU General Public
# 013494.python.hook-frictionless.line5.comment License (version 2.0 or later).
# 013495.python.hook-frictionless.line6.comment
# 013496.python.hook-frictionless.line7.comment The full license is available in LICENSE, distributed with
# 013497.python.hook-frictionless.line8.comment this software.
# 013498.python.hook-frictionless.line9.comment
# 013499.python.hook-frictionless.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013500.python.hook-frictionless.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 013501.python.hook-frictionless.line15.comment Collect data files in frictionless/assets
datas = collect_data_files('frictionless')

# 013502.python.hook-frictionless.line18.comment Collect modules from `frictionless.plugins` (programmatic imports).
hiddenimports = collect_submodules('frictionless.plugins')
