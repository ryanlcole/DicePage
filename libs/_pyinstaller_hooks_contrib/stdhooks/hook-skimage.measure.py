# 016867.python.hook-skimage.measure.line1.comment ------------------------------------------------------------------
# 016868.python.hook-skimage.measure.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 016869.python.hook-skimage.measure.line3.comment
# 016870.python.hook-skimage.measure.line4.comment This file is distributed under the terms of the GNU General Public
# 016871.python.hook-skimage.measure.line5.comment License (version 2.0 or later).
# 016872.python.hook-skimage.measure.line6.comment
# 016873.python.hook-skimage.measure.line7.comment The full license is available in LICENSE, distributed with
# 016874.python.hook-skimage.measure.line8.comment this software.
# 016875.python.hook-skimage.measure.line9.comment
# 016876.python.hook-skimage.measure.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016877.python.hook-skimage.measure.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies, collect_data_files, collect_submodules

# 016878.python.hook-skimage.measure.line15.comment As of scikit-image 0.22.0, we need to collect the __init__.pyi file for `lazy_loader`, as well as collect submodules
# 016879.python.hook-skimage.measure.line16.comment due to lazy loading.
if is_module_satisfies("scikit-image >= 0.22.0"):
    datas = collect_data_files("skimage.measure", includes=["*.pyi"])
    hiddenimports = collect_submodules('skimage.measure', filter=lambda name: name != 'skimage.measure.tests')
