# 020341.python.hook-zoneinfo.line1.comment ------------------------------------------------------------------
# 020342.python.hook-zoneinfo.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 020343.python.hook-zoneinfo.line3.comment
# 020344.python.hook-zoneinfo.line4.comment This file is distributed under the terms of the GNU General Public
# 020345.python.hook-zoneinfo.line5.comment License (version 2.0 or later).
# 020346.python.hook-zoneinfo.line6.comment
# 020347.python.hook-zoneinfo.line7.comment The full license is available in LICENSE, distributed with
# 020348.python.hook-zoneinfo.line8.comment this software.
# 020349.python.hook-zoneinfo.line9.comment
# 020350.python.hook-zoneinfo.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 020351.python.hook-zoneinfo.line11.comment ------------------------------------------------------------------

from PyInstaller.compat import is_win

# 020352.python.hook-zoneinfo.line15.comment On Windows, timezone data is provided by the tzdata package that is
# 020353.python.hook-zoneinfo.line16.comment not directly loaded.
if is_win:
    hiddenimports = ['tzdata']
