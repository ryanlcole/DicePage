# 013950.python.hook-imageio.line1.comment ------------------------------------------------------------------
# 013951.python.hook-imageio.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 013952.python.hook-imageio.line3.comment
# 013953.python.hook-imageio.line4.comment This file is distributed under the terms of the GNU General Public
# 013954.python.hook-imageio.line5.comment License (version 2.0 or later).
# 013955.python.hook-imageio.line6.comment
# 013956.python.hook-imageio.line7.comment The full license is available in LICENSE, distributed with
# 013957.python.hook-imageio.line8.comment this software.
# 013958.python.hook-imageio.line9.comment
# 013959.python.hook-imageio.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013960.python.hook-imageio.line11.comment ------------------------------------------------------------------

# 013961.python.hook-imageio.line13.comment Hook for imageio: http://imageio.github.io/

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = collect_data_files('imageio', subdir="resources")

# 013962.python.hook-imageio.line19.comment imageio plugins are imported lazily since ImageIO version 2.11.0.
# 013963.python.hook-imageio.line20.comment They are very light-weight, so we can safely include all of them.
hiddenimports = collect_submodules('imageio.plugins')
