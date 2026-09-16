# 005494.python.hook-gi.line1.comment -----------------------------------------------------------------------------
# 005495.python.hook-gi.line2.comment Copyright (c) 2005-2023, PyInstaller Development Team.
# 005496.python.hook-gi.line3.comment
# 005497.python.hook-gi.line4.comment Distributed under the terms of the GNU General Public License (version 2
# 005498.python.hook-gi.line5.comment or later) with exception for distributing the bootloader.
# 005499.python.hook-gi.line6.comment
# 005500.python.hook-gi.line7.comment The full license is in the file COPYING.txt, distributed with this software.
# 005501.python.hook-gi.line8.comment
# 005502.python.hook-gi.line9.comment SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
# 005503.python.hook-gi.line10.comment -----------------------------------------------------------------------------

from PyInstaller import compat
from packaging.version import Version

pygobject_version = Version(compat.importlib_metadata.version("pygobject")).release

hiddenimports = ['gi._error', 'gi._option']

# 005504.python.hook-gi.line19.comment PyGObject 3.50.0 added support for `asyncio`, and attempts to import inside the `_gi` extension.
if pygobject_version >= (3, 50, 0):
    hiddenimports += ['asyncio']

# 005505.python.hook-gi.line23.comment PyGobject 3.52.0 added `gi._enum`, which needs to be added to hiddenimports due to being imported from the
# 005506.python.hook-gi.line24.comment `_gi` extension.
if pygobject_version >= (3, 52, 0):
    hiddenimports += ['gi._enum']
