# 017574.python.hook-tkinterweb_tkhtml.line1.comment ------------------------------------------------------------------
# 017575.python.hook-tkinterweb_tkhtml.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 017576.python.hook-tkinterweb_tkhtml.line3.comment
# 017577.python.hook-tkinterweb_tkhtml.line4.comment This file is distributed under the terms of the GNU General Public
# 017578.python.hook-tkinterweb_tkhtml.line5.comment License (version 2.0 or later).
# 017579.python.hook-tkinterweb_tkhtml.line6.comment
# 017580.python.hook-tkinterweb_tkhtml.line7.comment The full license is available in LICENSE, distributed with
# 017581.python.hook-tkinterweb_tkhtml.line8.comment this software.
# 017582.python.hook-tkinterweb_tkhtml.line9.comment
# 017583.python.hook-tkinterweb_tkhtml.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017584.python.hook-tkinterweb_tkhtml.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# 017585.python.hook-tkinterweb_tkhtml.line15.comment Collect files from 'tkhtml'
datas = collect_data_files('tkinterweb_tkhtml')

# 017586.python.hook-tkinterweb_tkhtml.line18.comment Collect binaries from 'tkhtml'
binaries = collect_dynamic_libs('tkinterweb_tkhtml')
