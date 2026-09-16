# 016771.python.hook-skimage.draw.line1.comment ------------------------------------------------------------------
# 016772.python.hook-skimage.draw.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 016773.python.hook-skimage.draw.line3.comment
# 016774.python.hook-skimage.draw.line4.comment This file is distributed under the terms of the GNU General Public
# 016775.python.hook-skimage.draw.line5.comment License (version 2.0 or later).
# 016776.python.hook-skimage.draw.line6.comment
# 016777.python.hook-skimage.draw.line7.comment The full license is available in LICENSE, distributed with
# 016778.python.hook-skimage.draw.line8.comment this software.
# 016779.python.hook-skimage.draw.line9.comment
# 016780.python.hook-skimage.draw.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016781.python.hook-skimage.draw.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies, collect_data_files, collect_submodules

# 016782.python.hook-skimage.draw.line15.comment As of scikit-image 0.21.0, we need to collect the __init__.pyi file for `lazy_loader`, as well as collect submodules
# 016783.python.hook-skimage.draw.line16.comment due to lazy loading.
if is_module_satisfies("scikit-image >= 0.21.0"):
    datas = collect_data_files("skimage.draw", includes=["*.pyi"])
    hiddenimports = collect_submodules('skimage.draw', filter=lambda name: name != 'skimage.draw.tests')
