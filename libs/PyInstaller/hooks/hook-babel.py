# 005295.python.hook-babel.line1.comment -----------------------------------------------------------------------------
# 005296.python.hook-babel.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 005297.python.hook-babel.line3.comment
# 005298.python.hook-babel.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005299.python.hook-babel.line5.comment or later) with exception for distributing the bootloader.
# 005300.python.hook-babel.line6.comment
# 005301.python.hook-babel.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005302.python.hook-babel.line8.comment
# 005303.python.hook-babel.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005304.python.hook-babel.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_data_files

# 005305.python.hook-babel.line14.comment Ensure that .dat files from locale-data sub-directory are collected.
datas = collect_data_files('babel')

# 005306.python.hook-babel.line17.comment Unpickling of locale-data/root.dat currently (babel v2.16.0) requires classes from following modules, so ensure that
# 005307.python.hook-babel.line18.comment they are always collected:
hiddenimports = [
    "babel.dates",
    "babel.localedata",
    "babel.plural",
    "babel.numbers",
]
