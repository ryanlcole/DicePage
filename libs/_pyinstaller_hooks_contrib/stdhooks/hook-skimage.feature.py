# 016797.python.hook-skimage.feature.line1.comment ------------------------------------------------------------------
# 016798.python.hook-skimage.feature.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 016799.python.hook-skimage.feature.line3.comment
# 016800.python.hook-skimage.feature.line4.comment This file is distributed under the terms of the GNU General Public
# 016801.python.hook-skimage.feature.line5.comment License (version 2.0 or later).
# 016802.python.hook-skimage.feature.line6.comment
# 016803.python.hook-skimage.feature.line7.comment The full license is available in LICENSE, distributed with
# 016804.python.hook-skimage.feature.line8.comment this software.
# 016805.python.hook-skimage.feature.line9.comment
# 016806.python.hook-skimage.feature.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016807.python.hook-skimage.feature.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies, collect_data_files, collect_submodules

# 016808.python.hook-skimage.feature.line15.comment The following missing module prevents import of skimage.feature with skimage 0.17.x.
hiddenimports = ['skimage.feature._orb_descriptor_positions', ]

# 016809.python.hook-skimage.feature.line18.comment Collect the data file with ORB descriptor positions. In earlier versions of scikit-image, this file was in
# 016810.python.hook-skimage.feature.line19.comment `skimage/data` directory, and it was moved to `skimage/feature` in v0.17.0. Collect if from wherever it is.
datas = collect_data_files('skimage', includes=['**/orb_descriptor_positions.txt'])

# 016811.python.hook-skimage.feature.line22.comment As of scikit-image 0.22.0, we need to collect the __init__.pyi file for `lazy_loader`, as well as collect submodules
# 016812.python.hook-skimage.feature.line23.comment due to lazy loading.
if is_module_satisfies("scikit-image >= 0.22.0"):
    datas += collect_data_files("skimage.feature", includes=["*.pyi"])
    hiddenimports = collect_submodules('skimage.feature', filter=lambda name: name != 'skimage.feature.tests')
