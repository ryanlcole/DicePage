# 015978.python.hook-pymorphy3.line1.comment ------------------------------------------------------------------
# 015979.python.hook-pymorphy3.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 015980.python.hook-pymorphy3.line3.comment
# 015981.python.hook-pymorphy3.line4.comment This file is distributed under the terms of the GNU General Public
# 015982.python.hook-pymorphy3.line5.comment License (version 2.0 or later).
# 015983.python.hook-pymorphy3.line6.comment
# 015984.python.hook-pymorphy3.line7.comment The full license is available in LICENSE, distributed with
# 015985.python.hook-pymorphy3.line8.comment this software.
# 015986.python.hook-pymorphy3.line9.comment
# 015987.python.hook-pymorphy3.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015988.python.hook-pymorphy3.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import can_import_module, copy_metadata, collect_data_files

datas = copy_metadata('pymorphy3_dicts_ru')
datas += collect_data_files('pymorphy3_dicts_ru')

hiddenimports = ['pymorphy3_dicts_ru']

# 015989.python.hook-pymorphy3.line20.comment Check if the Ukrainian model is installed
if can_import_module('pymorphy3_dicts_uk'):
    datas += copy_metadata('pymorphy3_dicts_uk')
    datas += collect_data_files('pymorphy3_dicts_uk')

    hiddenimports += ['pymorphy3_dicts_uk']
