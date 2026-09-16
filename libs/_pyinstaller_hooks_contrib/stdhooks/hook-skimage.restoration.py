# 016930.python.hook-skimage.restoration.line1.comment ------------------------------------------------------------------
# 016931.python.hook-skimage.restoration.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 016932.python.hook-skimage.restoration.line3.comment
# 016933.python.hook-skimage.restoration.line4.comment This file is distributed under the terms of the GNU General Public
# 016934.python.hook-skimage.restoration.line5.comment License (version 2.0 or later).
# 016935.python.hook-skimage.restoration.line6.comment
# 016936.python.hook-skimage.restoration.line7.comment The full license is available in LICENSE, distributed with
# 016937.python.hook-skimage.restoration.line8.comment this software.
# 016938.python.hook-skimage.restoration.line9.comment
# 016939.python.hook-skimage.restoration.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016940.python.hook-skimage.restoration.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies, collect_data_files, collect_submodules

# 016941.python.hook-skimage.restoration.line15.comment As of scikit-image 0.22.0, we need to collect the __init__.pyi file for `lazy_loader`, as well as collect submodules
# 016942.python.hook-skimage.restoration.line16.comment due to lazy loading.
if is_module_satisfies("scikit-image >= 0.22.0"):
    datas = collect_data_files("skimage.restoration", includes=["*.pyi"])
    hiddenimports = collect_submodules('skimage.restoration', filter=lambda name: name != 'skimage.restoration.tests')
