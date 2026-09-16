# 016905.python.hook-skimage.line1.comment ------------------------------------------------------------------
# 016906.python.hook-skimage.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 016907.python.hook-skimage.line3.comment
# 016908.python.hook-skimage.line4.comment This file is distributed under the terms of the GNU General Public
# 016909.python.hook-skimage.line5.comment License (version 2.0 or later).
# 016910.python.hook-skimage.line6.comment
# 016911.python.hook-skimage.line7.comment The full license is available in LICENSE, distributed with
# 016912.python.hook-skimage.line8.comment this software.
# 016913.python.hook-skimage.line9.comment
# 016914.python.hook-skimage.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016915.python.hook-skimage.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, is_module_satisfies

# 016916.python.hook-skimage.line15.comment As of scikit-image 0.20.0, we need to collect the __init__.pyi file for `lazy_loader`.
if is_module_satisfies('scikit-image >= 0.20.0'):
    datas = collect_data_files("skimage", includes=["*.pyi"])
