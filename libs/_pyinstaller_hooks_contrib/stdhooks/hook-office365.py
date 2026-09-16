# 015071.python.hook-office365.line1.comment ------------------------------------------------------------------
# 015072.python.hook-office365.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 015073.python.hook-office365.line3.comment
# 015074.python.hook-office365.line4.comment This file is distributed under the terms of the GNU General Public
# 015075.python.hook-office365.line5.comment License (version 2.0 or later).
# 015076.python.hook-office365.line6.comment
# 015077.python.hook-office365.line7.comment The full license is available in LICENSE, distributed with
# 015078.python.hook-office365.line8.comment this software.
# 015079.python.hook-office365.line9.comment
# 015080.python.hook-office365.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015081.python.hook-office365.line11.comment ------------------------------------------------------------------
"""
Office365-REST-Python-Client contains xml templates that are needed by some methods
This hook ensures that all of the data used by the package is bundled
"""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("office365")
