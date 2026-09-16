# 016608.python.hook-schwifty.line1.comment ------------------------------------------------------------------
# 016609.python.hook-schwifty.line2.comment Copyright (c) 2024 PyInstaller Development Team.
# 016610.python.hook-schwifty.line3.comment
# 016611.python.hook-schwifty.line4.comment This file is distributed under the terms of the GNU General Public
# 016612.python.hook-schwifty.line5.comment License (version 2.0 or later).
# 016613.python.hook-schwifty.line6.comment
# 016614.python.hook-schwifty.line7.comment The full license is available in LICENSE, distributed with
# 016615.python.hook-schwifty.line8.comment this software.
# 016616.python.hook-schwifty.line9.comment
# 016617.python.hook-schwifty.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016618.python.hook-schwifty.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import copy_metadata, collect_data_files

datas = copy_metadata('schwifty')
datas += collect_data_files('schwifty')
