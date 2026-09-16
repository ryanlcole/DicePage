# 014504.python.hook-mariadb.line1.comment ------------------------------------------------------------------
# 014505.python.hook-mariadb.line2.comment Copyright (c) 2021 PyInstaller Development Team.
# 014506.python.hook-mariadb.line3.comment
# 014507.python.hook-mariadb.line4.comment This file is distributed under the terms of the GNU General Public
# 014508.python.hook-mariadb.line5.comment License (version 2.0 or later).
# 014509.python.hook-mariadb.line6.comment
# 014510.python.hook-mariadb.line7.comment The full license is available in LICENSE, distributed with
# 014511.python.hook-mariadb.line8.comment this software.
# 014512.python.hook-mariadb.line9.comment
# 014513.python.hook-mariadb.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 014514.python.hook-mariadb.line11.comment ------------------------------------------------------------------

from PyInstaller.utils.hooks import is_module_satisfies, collect_submodules

# 014515.python.hook-mariadb.line15.comment The MariaDB uses a .pyd file that imports ``decimal`` module within its
# 014516.python.hook-mariadb.line16.comment module initialization function. On recent python versions (> 3.8), the decimal
# 014517.python.hook-mariadb.line17.comment module seems to be picked up nevertheless (presumably due to import in some
# 014518.python.hook-mariadb.line18.comment other module), but it is better not to rely on that, and ensure it is always
# 014519.python.hook-mariadb.line19.comment collected as a hidden import.
hiddenimports = ['decimal']

# 014520.python.hook-mariadb.line22.comment mariadb >= 1.1.0 requires several hidden imports from mariadb.constants.
# 014521.python.hook-mariadb.line23.comment Collect them all, just to be on the safe side...
if is_module_satisfies("mariadb >= 1.1.0"):
    hiddenimports += collect_submodules("mariadb.constants")
