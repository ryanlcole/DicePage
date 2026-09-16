# 016943.python.hook-skimage.transform.line1.comment ------------------------------------------------------------------
# 016944.python.hook-skimage.transform.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016945.python.hook-skimage.transform.line3.comment
# 016946.python.hook-skimage.transform.line4.comment This file is distributed under the terms of the GNU General Public
# 016947.python.hook-skimage.transform.line5.comment License (version 2.0 or later).
# 016948.python.hook-skimage.transform.line6.comment
# 016949.python.hook-skimage.transform.line7.comment The full license is available in LICENSE, distributed with
# 016950.python.hook-skimage.transform.line8.comment this software.
# 016951.python.hook-skimage.transform.line9.comment
# 016952.python.hook-skimage.transform.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016953.python.hook-skimage.transform.line11.comment ------------------------------------------------------------------
from PyInstaller.utils.hooks import is_module_satisfies, collect_data_files, collect_submodules

# 016954.python.hook-skimage.transform.line14.comment Hook tested with scikit-image (skimage) 0.9.3 on Mac OS 10.9 and Windows 7 64-bit
hiddenimports = ['skimage.draw.draw',
                 'skimage._shared.geometry',
                 'skimage._shared.transform',
                 'skimage.filters.rank.core_cy']

# 016955.python.hook-skimage.transform.line20.comment As of scikit-image 0.22.0, we need to collect the __init__.pyi file for `lazy_loader`, as well as collect submodules
# 016956.python.hook-skimage.transform.line21.comment due to lazy loading.
if is_module_satisfies("scikit-image >= 0.22.0"):
    datas = collect_data_files("skimage.transform", includes=["*.pyi"])
    hiddenimports += collect_submodules('skimage.transform', filter=lambda name: name != 'skimage.transform.tests')
