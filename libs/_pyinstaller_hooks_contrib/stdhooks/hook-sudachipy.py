# 017312.python.hook-sudachipy.line1.comment ------------------------------------------------------------------
# 017313.python.hook-sudachipy.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 017314.python.hook-sudachipy.line3.comment
# 017315.python.hook-sudachipy.line4.comment This file is distributed under the terms of the GNU General Public
# 017316.python.hook-sudachipy.line5.comment License (version 2.0 or later).
# 017317.python.hook-sudachipy.line6.comment
# 017318.python.hook-sudachipy.line7.comment The full license is available in LICENSE, distributed with
# 017319.python.hook-sudachipy.line8.comment this software.
# 017320.python.hook-sudachipy.line9.comment
# 017321.python.hook-sudachipy.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017322.python.hook-sudachipy.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import can_import_module, collect_data_files, is_module_satisfies

datas = collect_data_files('sudachipy')
hiddenimports = []

# 017323.python.hook-sudachipy.line18.comment In v0.6.8, `sudachipy.config` and `sudachipy.errors` modules were added, and are referenced from binary extension.
if is_module_satisfies('sudachipy >= 0.6.8'):
    hiddenimports += [
        'sudachipy.config',
        'sudachipy.errors',
    ]

# 017324.python.hook-sudachipy.line25.comment Check which types of dictionary are installed
for sudachi_dict in ['sudachidict_small', 'sudachidict_core', 'sudachidict_full']:
    if can_import_module(sudachi_dict):
        datas += collect_data_files(sudachi_dict)

        hiddenimports += [sudachi_dict]
