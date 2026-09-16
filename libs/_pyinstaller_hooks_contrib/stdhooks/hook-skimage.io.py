# 016854.python.hook-skimage.io.line1.comment ------------------------------------------------------------------
# 016855.python.hook-skimage.io.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016856.python.hook-skimage.io.line3.comment
# 016857.python.hook-skimage.io.line4.comment This file is distributed under the terms of the GNU General Public
# 016858.python.hook-skimage.io.line5.comment License (version 2.0 or later).
# 016859.python.hook-skimage.io.line6.comment
# 016860.python.hook-skimage.io.line7.comment The full license is available in LICENSE, distributed with
# 016861.python.hook-skimage.io.line8.comment this software.
# 016862.python.hook-skimage.io.line9.comment
# 016863.python.hook-skimage.io.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016864.python.hook-skimage.io.line11.comment ------------------------------------------------------------------

# 016865.python.hook-skimage.io.line13.comment This hook was tested with scikit-image (skimage) 0.14.1:
# 016866.python.hook-skimage.io.line14.comment https://scikit-image.org

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = collect_data_files("skimage.io._plugins")
hiddenimports = collect_submodules('skimage.io._plugins')
