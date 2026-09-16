# 005268.python.hook-_pyi_rth_utils.line1.comment -----------------------------------------------------------------------------
# 005269.python.hook-_pyi_rth_utils.line2.comment Copyright (c) 2023, PyInstaller Development Team.
# 005270.python.hook-_pyi_rth_utils.line3.comment
# 005271.python.hook-_pyi_rth_utils.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005272.python.hook-_pyi_rth_utils.line5.comment or later) with exception for distributing the bootloader.
# 005273.python.hook-_pyi_rth_utils.line6.comment
# 005274.python.hook-_pyi_rth_utils.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005275.python.hook-_pyi_rth_utils.line8.comment
# 005276.python.hook-_pyi_rth_utils.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005277.python.hook-_pyi_rth_utils.line10.comment -----------------------------------------------------------------------------

from PyInstaller import compat

# 005278.python.hook-_pyi_rth_utils.line14.comment Exclude submodules specific to non-applicable OSes
excludedimports = []
if not compat.is_win:
    excludedimports += ['_pyi_rth_utils._win32']
