# 006567.python.hook-platform.line1.comment -----------------------------------------------------------------------------
# 006568.python.hook-platform.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 006569.python.hook-platform.line3.comment
# 006570.python.hook-platform.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 006571.python.hook-platform.line5.comment or later) with exception for distributing the bootloader.
# 006572.python.hook-platform.line6.comment
# 006573.python.hook-platform.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 006574.python.hook-platform.line8.comment
# 006575.python.hook-platform.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 006576.python.hook-platform.line10.comment -----------------------------------------------------------------------------
import sys

# 006577.python.hook-platform.line13.comment see https://github.com/python/cpython/blob/3.9/Lib/platform.py#L411
# 006578.python.hook-platform.line14.comment This will exclude `plistlib` for sys.platform != 'darwin'
if sys.platform != 'darwin':
    excludedimports = ["plistlib"]
