# 018191.python.hook-ultralytics.line1.comment ------------------------------------------------------------------
# 018192.python.hook-ultralytics.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 018193.python.hook-ultralytics.line3.comment
# 018194.python.hook-ultralytics.line4.comment This file is distributed under the terms of the GNU General Public
# 018195.python.hook-ultralytics.line5.comment License (version 2.0 or later).
# 018196.python.hook-ultralytics.line6.comment
# 018197.python.hook-ultralytics.line7.comment The full license is available in LICENSE, distributed with
# 018198.python.hook-ultralytics.line8.comment this software.
# 018199.python.hook-ultralytics.line9.comment
# 018200.python.hook-ultralytics.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018201.python.hook-ultralytics.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

# 018202.python.hook-ultralytics.line15.comment Collect config .yaml files from ultralytics/cfg directory.
datas = collect_data_files('ultralytics')

# 018203.python.hook-ultralytics.line18.comment Collect source .py files for JIT/torchscript. Requires PyInstaller >= 5.3, no-op in older versions.
module_collection_mode = 'pyz+py'
