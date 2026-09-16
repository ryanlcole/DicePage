# 016880.python.hook-skimage.metrics.line1.comment ------------------------------------------------------------------
# 016881.python.hook-skimage.metrics.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 016882.python.hook-skimage.metrics.line3.comment
# 016883.python.hook-skimage.metrics.line4.comment This file is distributed under the terms of the GNU General Public
# 016884.python.hook-skimage.metrics.line5.comment License (version 2.0 or later).
# 016885.python.hook-skimage.metrics.line6.comment
# 016886.python.hook-skimage.metrics.line7.comment The full license is available in LICENSE, distributed with
# 016887.python.hook-skimage.metrics.line8.comment this software.
# 016888.python.hook-skimage.metrics.line9.comment
# 016889.python.hook-skimage.metrics.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016890.python.hook-skimage.metrics.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies, collect_data_files, collect_submodules

# 016891.python.hook-skimage.metrics.line15.comment As of scikit-image 0.23.0, we need to collect the __init__.pyi file for `lazy_loader`, as well as collect submodules
# 016892.python.hook-skimage.metrics.line16.comment due to lazy loading.
if is_module_satisfies("scikit-image >= 0.23.0"):
    datas = collect_data_files("skimage.metrics", includes=["*.pyi"])
    hiddenimports = collect_submodules('skimage.metrics', filter=lambda name: name != 'skimage.metrics.tests')
