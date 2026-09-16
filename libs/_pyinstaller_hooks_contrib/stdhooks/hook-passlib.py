# 015232.python.hook-passlib.line1.comment ------------------------------------------------------------------
# 015233.python.hook-passlib.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 015234.python.hook-passlib.line3.comment
# 015235.python.hook-passlib.line4.comment This file is distributed under the terms of the GNU General Public
# 015236.python.hook-passlib.line5.comment License (version 2.0 or later).
# 015237.python.hook-passlib.line6.comment
# 015238.python.hook-passlib.line7.comment The full license is available in LICENSE, distributed with
# 015239.python.hook-passlib.line8.comment this software.
# 015240.python.hook-passlib.line9.comment
# 015241.python.hook-passlib.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 015242.python.hook-passlib.line11.comment ------------------------------------------------------------------

# 015243.python.hook-passlib.line13.comment Handlers are imported by a lazy-load proxy, based on a
# 015244.python.hook-passlib.line14.comment name-to-package mapping. Collect all handlers to ease packaging.
# 015245.python.hook-passlib.line15.comment If you want to reduce the size of your application, used
# 015246.python.hook-passlib.line16.comment `--exclude-module` to remove unused ones.
hiddenimports = [
    "passlib.handlers",
    "passlib.handlers.digests",
    "configparser",
]
