# 017229.python.hook-spiceypy.line1.comment ------------------------------------------------------------------
# 017230.python.hook-spiceypy.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 017231.python.hook-spiceypy.line3.comment
# 017232.python.hook-spiceypy.line4.comment This file is distributed under the terms of the GNU General Public
# 017233.python.hook-spiceypy.line5.comment License (version 2.0 or later).
# 017234.python.hook-spiceypy.line6.comment
# 017235.python.hook-spiceypy.line7.comment The full license is available in LICENSE, distributed with
# 017236.python.hook-spiceypy.line8.comment this software.
# 017237.python.hook-spiceypy.line9.comment
# 017238.python.hook-spiceypy.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 017239.python.hook-spiceypy.line11.comment ------------------------------------------------------------------

# 017240.python.hook-spiceypy.line13.comment Hook for spiceypy: https://pypi.org/project/spiceypy/
# 017241.python.hook-spiceypy.line14.comment Tested on Ubuntu 20.04 with spiceypy 5.1.1

from PyInstaller.utils.hooks import collect_dynamic_libs

binaries = collect_dynamic_libs("spiceypy")
