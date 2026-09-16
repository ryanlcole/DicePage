# 006498.python.hook-pandas.plotting.line1.comment -----------------------------------------------------------------------------
# 006499.python.hook-pandas.plotting.line2.comment Copyright (c) 2021-2023, PyInstaller Development Team.
# 006500.python.hook-pandas.plotting.line3.comment
# 006501.python.hook-pandas.plotting.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006502.python.hook-pandas.plotting.line5.comment or later) with exception for distributing the bootloader.
# 006503.python.hook-pandas.plotting.line6.comment
# 006504.python.hook-pandas.plotting.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006505.python.hook-pandas.plotting.line8.comment
# 006506.python.hook-pandas.plotting.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006507.python.hook-pandas.plotting.line10.comment -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import check_requirement

# 006508.python.hook-pandas.plotting.line14.comment Starting with pandas 1.3.0, pandas.plotting._matplotlib is imported via importlib.import_module() and needs to be
# 006509.python.hook-pandas.plotting.line15.comment added to hidden imports. But do this only if matplotlib is available in the first place (as it is soft dependency
# 006510.python.hook-pandas.plotting.line16.comment of pandas).
if check_requirement('pandas >= 1.3.0') and check_requirement('matplotlib'):
    hiddenimports = ['pandas.plotting._matplotlib']
