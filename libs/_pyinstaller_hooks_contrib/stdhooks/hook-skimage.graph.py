# 016840.python.hook-skimage.graph.line1.comment ------------------------------------------------------------------
# 016841.python.hook-skimage.graph.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016842.python.hook-skimage.graph.line3.comment
# 016843.python.hook-skimage.graph.line4.comment This file is distributed under the terms of the GNU General Public
# 016844.python.hook-skimage.graph.line5.comment License (version 2.0 or later).
# 016845.python.hook-skimage.graph.line6.comment
# 016846.python.hook-skimage.graph.line7.comment The full license is available in LICENSE, distributed with
# 016847.python.hook-skimage.graph.line8.comment this software.
# 016848.python.hook-skimage.graph.line9.comment
# 016849.python.hook-skimage.graph.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016850.python.hook-skimage.graph.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies, collect_data_files, collect_submodules

# 016851.python.hook-skimage.graph.line15.comment The following missing module prevents import of skimage.graph with skimage 0.17.x.
hiddenimports = ['skimage.graph.heap', ]

# 016852.python.hook-skimage.graph.line18.comment As of scikit-image 0.22.0, we need to collect the __init__.pyi file for `lazy_loader`, as well as collect submodules
# 016853.python.hook-skimage.graph.line19.comment due to lazy loading.
if is_module_satisfies("scikit-image >= 0.22.0"):
    datas = collect_data_files("skimage.graph", includes=["*.pyi"])
    hiddenimports = collect_submodules('skimage.graph', filter=lambda name: name != 'skimage.graph.tests')
