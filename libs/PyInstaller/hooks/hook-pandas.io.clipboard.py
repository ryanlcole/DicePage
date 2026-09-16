# 006469.python.hook-pandas.io.clipboard.line1.comment -----------------------------------------------------------------------------
# 006470.python.hook-pandas.io.clipboard.line2.comment Copyright (c) 2024, PyInstaller Development Team.
# 006471.python.hook-pandas.io.clipboard.line3.comment
# 006472.python.hook-pandas.io.clipboard.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006473.python.hook-pandas.io.clipboard.line5.comment or later) with exception for distributing the bootloader.
# 006474.python.hook-pandas.io.clipboard.line6.comment
# 006475.python.hook-pandas.io.clipboard.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006476.python.hook-pandas.io.clipboard.line8.comment
# 006477.python.hook-pandas.io.clipboard.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006478.python.hook-pandas.io.clipboard.line10.comment -----------------------------------------------------------------------------

# 006479.python.hook-pandas.io.clipboard.line12.comment This module conditionally imports PyQt5:
# 006480.python.hook-pandas.io.clipboard.line13.comment https://github.com/pandas-dev/pandas/blob/95308514e1221200e4526dfaf248283f3d7ade06/pandas/io/clipboard/__init__.py#L578-L597
# 006481.python.hook-pandas.io.clipboard.line14.comment Suppress this import to prevent PyQt5 from being accidentally pulled in; the actually relevant Qt bindings are
# 006482.python.hook-pandas.io.clipboard.line15.comment determined by our hook for `qtpy` module, which contemporary versions of pandas mandate as part of `clipboard` and
# 006483.python.hook-pandas.io.clipboard.line16.comment `all` extras:
# 006484.python.hook-pandas.io.clipboard.line17.comment https://github.com/pandas-dev/pandas/blob/95308514e1221200e4526dfaf248283f3d7ade06/pyproject.toml#L86
# 006485.python.hook-pandas.io.clipboard.line18.comment https://github.com/pandas-dev/pandas/blob/95308514e1221200e4526dfaf248283f3d7ade06/pyproject.toml#L115
excludedimports = ['PyQt5']
