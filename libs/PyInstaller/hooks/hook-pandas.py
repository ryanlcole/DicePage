# 006511.python.hook-pandas.line1.comment -----------------------------------------------------------------------------
# 006512.python.hook-pandas.line2.comment Copyright (c) 2017-2023, PyInstaller Development Team.
# 006513.python.hook-pandas.line3.comment
# 006514.python.hook-pandas.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006515.python.hook-pandas.line5.comment or later) with exception for distributing the bootloader.
# 006516.python.hook-pandas.line6.comment
# 006517.python.hook-pandas.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006518.python.hook-pandas.line8.comment
# 006519.python.hook-pandas.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006520.python.hook-pandas.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules, check_requirement

# 006521.python.hook-pandas.line14.comment Pandas keeps Python extensions loaded with dynamic imports here.
hiddenimports = collect_submodules('pandas._libs')

# 006522.python.hook-pandas.line17.comment Pandas 1.2.0 and later require cmath hidden import on linux and macOS. On Windows, this is not strictly required, but
# 006523.python.hook-pandas.line18.comment we add it anyway to keep things simple (and future-proof).
if check_requirement('pandas >= 1.2.0'):
    hiddenimports += ['cmath']
