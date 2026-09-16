# 015879.python.hook-pylibmagic.line1.comment ------------------------------------------------------------------
# 015880.python.hook-pylibmagic.line2.comment Copyright (c) 2023 PyInstaller Development Team.
# 015881.python.hook-pylibmagic.line3.comment
# 015882.python.hook-pylibmagic.line4.comment This file is distributed under the terms of the GNU General Public
# 015883.python.hook-pylibmagic.line5.comment License (version 2.0 or later).
# 015884.python.hook-pylibmagic.line6.comment
# 015885.python.hook-pylibmagic.line7.comment The full license is available in LICENSE, distributed with
# 015886.python.hook-pylibmagic.line8.comment this software.
# 015887.python.hook-pylibmagic.line9.comment
# 015888.python.hook-pylibmagic.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015889.python.hook-pylibmagic.line11.comment ------------------------------------------------------------------
"""
Pylibmagic contains data files (libmagic compiled and configurations) required to use the python-magic package.
"""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("pylibmagic")
