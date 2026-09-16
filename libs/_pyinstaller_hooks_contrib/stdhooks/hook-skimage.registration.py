# 016917.python.hook-skimage.registration.line1.comment ------------------------------------------------------------------
# 016918.python.hook-skimage.registration.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 016919.python.hook-skimage.registration.line3.comment
# 016920.python.hook-skimage.registration.line4.comment This file is distributed under the terms of the GNU General Public
# 016921.python.hook-skimage.registration.line5.comment License (version 2.0 or later).
# 016922.python.hook-skimage.registration.line6.comment
# 016923.python.hook-skimage.registration.line7.comment The full license is available in LICENSE, distributed with
# 016924.python.hook-skimage.registration.line8.comment this software.
# 016925.python.hook-skimage.registration.line9.comment
# 016926.python.hook-skimage.registration.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016927.python.hook-skimage.registration.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies, collect_data_files, collect_submodules

# 016928.python.hook-skimage.registration.line15.comment As of scikit-image 0.22.0, we need to collect the __init__.pyi file for `lazy_loader`, as well as collect submodules
# 016929.python.hook-skimage.registration.line16.comment due to lazy loading.
if is_module_satisfies("scikit-image >= 0.22.0"):
    datas = collect_data_files("skimage.registration", includes=["*.pyi"])
    hiddenimports = collect_submodules('skimage.registration', filter=lambda name: name != 'skimage.registration.tests')
