# 016784.python.hook-skimage.exposure.line1.comment ------------------------------------------------------------------
# 016785.python.hook-skimage.exposure.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 016786.python.hook-skimage.exposure.line3.comment
# 016787.python.hook-skimage.exposure.line4.comment This file is distributed under the terms of the GNU General Public
# 016788.python.hook-skimage.exposure.line5.comment License (version 2.0 or later).
# 016789.python.hook-skimage.exposure.line6.comment
# 016790.python.hook-skimage.exposure.line7.comment The full license is available in LICENSE, distributed with
# 016791.python.hook-skimage.exposure.line8.comment this software.
# 016792.python.hook-skimage.exposure.line9.comment
# 016793.python.hook-skimage.exposure.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016794.python.hook-skimage.exposure.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies, collect_data_files, collect_submodules

# 016795.python.hook-skimage.exposure.line15.comment As of scikit-image 0.21.0, we need to collect the __init__.pyi file for `lazy_loader`, as well as collect submodules
# 016796.python.hook-skimage.exposure.line16.comment due to lazy loading.
if is_module_satisfies("scikit-image >= 0.21.0"):
    datas = collect_data_files("skimage.exposure", includes=["*.pyi"])
    hiddenimports = collect_submodules('skimage.exposure', filter=lambda name: name != 'skimage.exposure.tests')
