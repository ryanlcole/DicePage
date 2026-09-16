# 012195.python.hook-backports.zoneinfo.line1.comment ------------------------------------------------------------------
# 012196.python.hook-backports.zoneinfo.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 012197.python.hook-backports.zoneinfo.line3.comment
# 012198.python.hook-backports.zoneinfo.line4.comment This file is distributed under the terms of the GNU General Public
# 012199.python.hook-backports.zoneinfo.line5.comment License (version 2.0 or later).
# 012200.python.hook-backports.zoneinfo.line6.comment
# 012201.python.hook-backports.zoneinfo.line7.comment The full license is available in LICENSE, distributed with
# 012202.python.hook-backports.zoneinfo.line8.comment this software.
# 012203.python.hook-backports.zoneinfo.line9.comment
# 012204.python.hook-backports.zoneinfo.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 012205.python.hook-backports.zoneinfo.line11.comment ------------------------------------------------------------------

from PyInstaller.compat import is_win

# 012206.python.hook-backports.zoneinfo.line15.comment On Windows, timezone data is provided by the tzdata package that is
# 012207.python.hook-backports.zoneinfo.line16.comment not directly loaded.
if is_win:
    hiddenimports = ['tzdata']
