# 014702.python.hook-names.line1.comment ------------------------------------------------------------------
# 014703.python.hook-names.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 014704.python.hook-names.line3.comment
# 014705.python.hook-names.line4.comment This file is distributed under the terms of the GNU General Public
# 014706.python.hook-names.line5.comment License (version 2.0 or later).
# 014707.python.hook-names.line6.comment
# 014708.python.hook-names.line7.comment The full license is available in LICENSE, distributed with
# 014709.python.hook-names.line8.comment this software.
# 014710.python.hook-names.line9.comment
# 014711.python.hook-names.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014712.python.hook-names.line11.comment ------------------------------------------------------------------

# 014713.python.hook-names.line13.comment names: generate random names
# 014714.python.hook-names.line14.comment Module PyPI Homepage: https://pypi.python.org/pypi/names/0.3.0

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('names')
