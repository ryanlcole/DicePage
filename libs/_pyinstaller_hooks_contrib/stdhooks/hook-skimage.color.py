# 016745.python.hook-skimage.color.line1.comment ------------------------------------------------------------------
# 016746.python.hook-skimage.color.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 016747.python.hook-skimage.color.line3.comment
# 016748.python.hook-skimage.color.line4.comment This file is distributed under the terms of the GNU General Public
# 016749.python.hook-skimage.color.line5.comment License (version 2.0 or later).
# 016750.python.hook-skimage.color.line6.comment
# 016751.python.hook-skimage.color.line7.comment The full license is available in LICENSE, distributed with
# 016752.python.hook-skimage.color.line8.comment this software.
# 016753.python.hook-skimage.color.line9.comment
# 016754.python.hook-skimage.color.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016755.python.hook-skimage.color.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies, collect_data_files, collect_submodules

# 016756.python.hook-skimage.color.line15.comment As of scikit-image 0.21.0, we need to collect the __init__.pyi file for `lazy_loader`, as well as collect submodules
# 016757.python.hook-skimage.color.line16.comment due to lazy loading.
if is_module_satisfies("scikit-image >= 0.21.0"):
    datas = collect_data_files("skimage.color", includes=["*.pyi"])
    hiddenimports = collect_submodules('skimage.color', filter=lambda name: name != 'skimage.color.tests')
