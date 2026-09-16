# 006941.python.hook-sqlite3.line1.comment -----------------------------------------------------------------------------
# 006942.python.hook-sqlite3.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 006943.python.hook-sqlite3.line3.comment
# 006944.python.hook-sqlite3.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006945.python.hook-sqlite3.line5.comment or later) with exception for distributing the bootloader.
# 006946.python.hook-sqlite3.line6.comment
# 006947.python.hook-sqlite3.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006948.python.hook-sqlite3.line8.comment
# 006949.python.hook-sqlite3.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006950.python.hook-sqlite3.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = []

# 006951.python.hook-sqlite3.line16.comment On Windows in Python 3.4 'sqlite3' package might contain tests that are not required in frozen application.
for mod in collect_submodules('sqlite3'):
    if not mod.startswith('sqlite3.test'):
        hiddenimports.append(mod)
