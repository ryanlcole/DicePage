# 015990.python.hook-pymssql.line1.comment ------------------------------------------------------------------
# 015991.python.hook-pymssql.line2.comment Copyright (c) 2020-2021 PyInstaller Development Team.
# 015992.python.hook-pymssql.line3.comment
# 015993.python.hook-pymssql.line4.comment This file is distributed under the terms of the GNU General Public
# 015994.python.hook-pymssql.line5.comment License (version 2.0 or later).
# 015995.python.hook-pymssql.line6.comment
# 015996.python.hook-pymssql.line7.comment The full license is available in LICENSE, distributed with
# 015997.python.hook-pymssql.line8.comment this software.
# 015998.python.hook-pymssql.line9.comment
# 015999.python.hook-pymssql.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 016000.python.hook-pymssql.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies

hiddenimports = ["decimal"]
# 016001.python.hook-pymssql.line16.comment In newer versions of pymssql,  the _mssql was under pymssql
if is_module_satisfies("pymssql > 2.1.5"):
    hiddenimports += ["pymssql._mssql", "uuid"]
else:
    hiddenimports += ["_mssql"]
