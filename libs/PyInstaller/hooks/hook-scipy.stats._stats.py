# 006778.python.hook-scipy.stats._stats.line1.comment -----------------------------------------------------------------------------
# 006779.python.hook-scipy.stats._stats.line2.comment Copyright (c) 2013-2023, PyInstaller Development Team.
# 006780.python.hook-scipy.stats._stats.line3.comment
# 006781.python.hook-scipy.stats._stats.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006782.python.hook-scipy.stats._stats.line5.comment or later) with exception for distributing the bootloader.
# 006783.python.hook-scipy.stats._stats.line6.comment
# 006784.python.hook-scipy.stats._stats.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006785.python.hook-scipy.stats._stats.line8.comment
# 006786.python.hook-scipy.stats._stats.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006787.python.hook-scipy.stats._stats.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import check_requirement

if check_requirement("scipy >= 1.5.0"):
    hiddenimports = ['scipy.special.cython_special']
