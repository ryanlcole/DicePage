# 016758.python.hook-skimage.data.line1.comment ------------------------------------------------------------------
# 016759.python.hook-skimage.data.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 016760.python.hook-skimage.data.line3.comment
# 016761.python.hook-skimage.data.line4.comment This file is distributed under the terms of the GNU General Public
# 016762.python.hook-skimage.data.line5.comment License (version 2.0 or later).
# 016763.python.hook-skimage.data.line6.comment
# 016764.python.hook-skimage.data.line7.comment The full license is available in LICENSE, distributed with
# 016765.python.hook-skimage.data.line8.comment this software.
# 016766.python.hook-skimage.data.line9.comment
# 016767.python.hook-skimage.data.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016768.python.hook-skimage.data.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies, collect_data_files, collect_submodules

# 016769.python.hook-skimage.data.line15.comment As of scikit-image 0.20.0, we need to collect the __init__.pyi file for `lazy_loader`, as well as collect submodules
# 016770.python.hook-skimage.data.line16.comment due to lazy loading.
if is_module_satisfies('scikit-image >= 0.20.0'):
    datas = collect_data_files("skimage.data", includes=["*.pyi"])
    hiddenimports = collect_submodules('skimage.data', filter=lambda name: name != 'skimage.data.tests')
