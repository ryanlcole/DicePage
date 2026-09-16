# 013478.python.hook-freetype.line1.comment ------------------------------------------------------------------
# 013479.python.hook-freetype.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 013480.python.hook-freetype.line3.comment
# 013481.python.hook-freetype.line4.comment This file is distributed under the terms of the GNU General Public
# 013482.python.hook-freetype.line5.comment License (version 2.0 or later).
# 013483.python.hook-freetype.line6.comment
# 013484.python.hook-freetype.line7.comment The full license is available in LICENSE, distributed with
# 013485.python.hook-freetype.line8.comment this software.
# 013486.python.hook-freetype.line9.comment
# 013487.python.hook-freetype.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 013488.python.hook-freetype.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_dynamic_libs

# 013489.python.hook-freetype.line15.comment Collect the bundled freetype shared library, if available.
binaries = collect_dynamic_libs('freetype')
