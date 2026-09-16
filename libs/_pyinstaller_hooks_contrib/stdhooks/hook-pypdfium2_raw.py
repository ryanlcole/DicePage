# 016063.python.hook-pypdfium2_raw.line1.comment ------------------------------------------------------------------
# 016064.python.hook-pypdfium2_raw.line2.comment Copyright (c) 2025 PyInstaller Development Team.
# 016065.python.hook-pypdfium2_raw.line3.comment
# 016066.python.hook-pypdfium2_raw.line4.comment This file is distributed under the terms of the GNU General Public
# 016067.python.hook-pypdfium2_raw.line5.comment License (version 2.0 or later).
# 016068.python.hook-pypdfium2_raw.line6.comment
# 016069.python.hook-pypdfium2_raw.line7.comment The full license is available in LICENSE, distributed with
# 016070.python.hook-pypdfium2_raw.line8.comment this software.
# 016071.python.hook-pypdfium2_raw.line9.comment
# 016072.python.hook-pypdfium2_raw.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016073.python.hook-pypdfium2_raw.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files

# 016074.python.hook-pypdfium2_raw.line15.comment Collect the bundled pdfium shared library.
binaries = collect_dynamic_libs('pypdfium2_raw')

# 016075.python.hook-pypdfium2_raw.line18.comment Collect `version.json`.
datas = collect_data_files("pypdfium2_raw")
