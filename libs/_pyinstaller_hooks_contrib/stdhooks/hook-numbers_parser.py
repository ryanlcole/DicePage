# 014896.python.hook-numbers_parser.line1.comment ------------------------------------------------------------------
# 014897.python.hook-numbers_parser.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 014898.python.hook-numbers_parser.line3.comment
# 014899.python.hook-numbers_parser.line4.comment This file is distributed under the terms of the GNU General Public
# 014900.python.hook-numbers_parser.line5.comment License (version 2.0 or later).
# 014901.python.hook-numbers_parser.line6.comment
# 014902.python.hook-numbers_parser.line7.comment The full license is available in LICENSE, distributed with
# 014903.python.hook-numbers_parser.line8.comment this software.
# 014904.python.hook-numbers_parser.line9.comment
# 014905.python.hook-numbers_parser.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014906.python.hook-numbers_parser.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

# 014907.python.hook-numbers_parser.line15.comment Ensure that `numbers_parser/data/empty.numbers` is collected.
datas = collect_data_files('numbers_parser')
