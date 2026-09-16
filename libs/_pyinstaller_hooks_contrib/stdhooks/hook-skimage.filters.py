# 016813.python.hook-skimage.filters.line1.comment ------------------------------------------------------------------
# 016814.python.hook-skimage.filters.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 016815.python.hook-skimage.filters.line3.comment
# 016816.python.hook-skimage.filters.line4.comment This file is distributed under the terms of the GNU General Public
# 016817.python.hook-skimage.filters.line5.comment License (version 2.0 or later).
# 016818.python.hook-skimage.filters.line6.comment
# 016819.python.hook-skimage.filters.line7.comment The full license is available in LICENSE, distributed with
# 016820.python.hook-skimage.filters.line8.comment this software.
# 016821.python.hook-skimage.filters.line9.comment
# 016822.python.hook-skimage.filters.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016823.python.hook-skimage.filters.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies, collect_data_files, collect_submodules

if is_module_satisfies("scikit-image >= 0.19.0"):
    # 016824.python.hook-skimage.filters.line16.comment In scikit-image 0.19.x, `skimage.filters` switched to lazy module loading, so we need to collect all submodules.
    hiddenimports = collect_submodules('skimage.filters', filter=lambda name: name != 'skimage.filters.tests')

    # 016825.python.hook-skimage.filters.line19.comment In scikit-image 0.20.0, `lazy_loader` is used, so we need to collect `__init__.pyi` file.
    if is_module_satisfies("scikit-image >= 0.20.0"):
        datas = collect_data_files("skimage.filters", includes=["*.pyi"])
elif is_module_satisfies("scikit-image >= 0.18.0"):
    # 016826.python.hook-skimage.filters.line23.comment The following missing module prevents import of skimage.feature with skimage 0.18.x.
    hiddenimports = ['skimage.filters.rank.core_cy_3d', ]
