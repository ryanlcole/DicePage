# 016827.python.hook-skimage.future.line1.comment ------------------------------------------------------------------
# 016828.python.hook-skimage.future.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 016829.python.hook-skimage.future.line3.comment
# 016830.python.hook-skimage.future.line4.comment This file is distributed under the terms of the GNU General Public
# 016831.python.hook-skimage.future.line5.comment License (version 2.0 or later).
# 016832.python.hook-skimage.future.line6.comment
# 016833.python.hook-skimage.future.line7.comment The full license is available in LICENSE, distributed with
# 016834.python.hook-skimage.future.line8.comment this software.
# 016835.python.hook-skimage.future.line9.comment
# 016836.python.hook-skimage.future.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016837.python.hook-skimage.future.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies, collect_data_files, collect_submodules

# 016838.python.hook-skimage.future.line15.comment As of scikit-image 0.21.0, we need to collect the __init__.pyi file for `lazy_loader`, as well as collect submodules
# 016839.python.hook-skimage.future.line16.comment due to lazy loading.
if is_module_satisfies("scikit-image >= 0.21.0"):
    datas = collect_data_files("skimage.future", includes=["*.pyi"])
    hiddenimports = collect_submodules('skimage.future', filter=lambda name: name != 'skimage.future.tests')
