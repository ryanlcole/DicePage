# 017854.python.hook-trame_iframe.line1.comment ------------------------------------------------------------------
# 017855.python.hook-trame_iframe.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 017856.python.hook-trame_iframe.line3.comment
# 017857.python.hook-trame_iframe.line4.comment This file is distributed under the terms of the GNU General Public
# 017858.python.hook-trame_iframe.line5.comment License (version 2.0 or later).
# 017859.python.hook-trame_iframe.line6.comment
# 017860.python.hook-trame_iframe.line7.comment The full license is available in LICENSE, distributed with
# 017861.python.hook-trame_iframe.line8.comment this software.
# 017862.python.hook-trame_iframe.line9.comment
# 017863.python.hook-trame_iframe.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017864.python.hook-trame_iframe.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("trame_iframe", subdir="module")
