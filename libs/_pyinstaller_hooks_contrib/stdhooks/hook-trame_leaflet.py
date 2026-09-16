# 017876.python.hook-trame_leaflet.line1.comment ------------------------------------------------------------------
# 017877.python.hook-trame_leaflet.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017878.python.hook-trame_leaflet.line3.comment
# 017879.python.hook-trame_leaflet.line4.comment This file is distributed under the terms of the GNU General Public
# 017880.python.hook-trame_leaflet.line5.comment License (version 2.0 or later).
# 017881.python.hook-trame_leaflet.line6.comment
# 017882.python.hook-trame_leaflet.line7.comment The full license is available in LICENSE, distributed with
# 017883.python.hook-trame_leaflet.line8.comment this software.
# 017884.python.hook-trame_leaflet.line9.comment
# 017885.python.hook-trame_leaflet.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017886.python.hook-trame_leaflet.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = [*collect_data_files("trame_leaflet", subdir="module")]
