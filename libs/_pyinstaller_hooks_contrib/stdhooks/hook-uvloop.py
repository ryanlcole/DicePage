# 018320.python.hook-uvloop.line1.comment ------------------------------------------------------------------
# 018321.python.hook-uvloop.line2.comment Copyright (c) 2020 PyInstaller Development Team.
# 018322.python.hook-uvloop.line3.comment
# 018323.python.hook-uvloop.line4.comment This file is distributed under the terms of the GNU General Public
# 018324.python.hook-uvloop.line5.comment License (version 2.0 or later).
# 018325.python.hook-uvloop.line6.comment
# 018326.python.hook-uvloop.line7.comment The full license is available in LICENSE, distributed with
# 018327.python.hook-uvloop.line8.comment this software.
# 018328.python.hook-uvloop.line9.comment
# 018329.python.hook-uvloop.line10.comment SPDX-License-Identifier: GPL-2.0-or-later
# 018330.python.hook-uvloop.line11.comment ------------------------------------------------------------------
# 018331.python.hook-uvloop.line12.comment
# 018332.python.hook-uvloop.line13.comment Hook for the uvloop package: https://pypi.python.org/pypi/uvloop
# 018333.python.hook-uvloop.line14.comment
# 018334.python.hook-uvloop.line15.comment Tested with uvloop 0.8.1 and Python 3.6.2, on Ubuntu 16.04.1 64bit.

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('uvloop')
