# 012637.python.hook-countryinfo.line1.comment ------------------------------------------------------------------
# 012638.python.hook-countryinfo.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 012639.python.hook-countryinfo.line3.comment
# 012640.python.hook-countryinfo.line4.comment This file is distributed under the terms of the GNU General Public
# 012641.python.hook-countryinfo.line5.comment License (version 2.0 or later).
# 012642.python.hook-countryinfo.line6.comment
# 012643.python.hook-countryinfo.line7.comment The full license is available in LICENSE, distributed with
# 012644.python.hook-countryinfo.line8.comment this software.
# 012645.python.hook-countryinfo.line9.comment
# 012646.python.hook-countryinfo.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012647.python.hook-countryinfo.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import copy_metadata, collect_data_files

datas = copy_metadata("countryinfo") + collect_data_files("countryinfo")
