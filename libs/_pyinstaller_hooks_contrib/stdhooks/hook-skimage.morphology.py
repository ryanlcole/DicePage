# 016893.python.hook-skimage.morphology.line1.comment ------------------------------------------------------------------
# 016894.python.hook-skimage.morphology.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 016895.python.hook-skimage.morphology.line3.comment
# 016896.python.hook-skimage.morphology.line4.comment This file is distributed under the terms of the GNU General Public
# 016897.python.hook-skimage.morphology.line5.comment License (version 2.0 or later).
# 016898.python.hook-skimage.morphology.line6.comment
# 016899.python.hook-skimage.morphology.line7.comment The full license is available in LICENSE, distributed with
# 016900.python.hook-skimage.morphology.line8.comment this software.
# 016901.python.hook-skimage.morphology.line9.comment
# 016902.python.hook-skimage.morphology.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016903.python.hook-skimage.morphology.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, is_module_satisfies

# 016904.python.hook-skimage.morphology.line15.comment As of scikit-image 0.20.0, we need to collect .npy data files for `skimage.morphology`
if is_module_satisfies('scikit-image >= 0.20'):
    datas = collect_data_files("skimage.morphology", includes=["*.npy"])
